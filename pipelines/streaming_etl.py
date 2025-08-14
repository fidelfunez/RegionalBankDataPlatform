#!/usr/bin/env python3
"""
Streaming ETL Pipeline for Regional Development Bank Data Platform

This script processes real-time streaming data including:
- Transaction data (microloans, payments)
- Remittance data (cross-border transfers)
- Real-time analytics and alerts

Author: Data Engineering Team
Date: 2024
"""

import sys
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.streaming import StreamingQuery
from pyspark.sql.functions import (
    col, from_json, to_json, struct, window, 
    count, sum as spark_sum, avg, max as spark_max,
    min as spark_min, current_timestamp, expr,
    when, lit, sha2, upper, trim, year, month, dayofmonth, coalesce
)
from pyspark.sql.types import (
    StructType, StructField, StringType, 
    DoubleType, IntegerType, TimestampType, BooleanType
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RegionalBankStreamingETL:
    """
    Streaming ETL class for processing real-time regional bank data
    """
    
    def __init__(self, spark: SparkSession, s3_bucket: str, kinesis_stream: str):
        self.spark = spark
        self.s3_bucket = s3_bucket
        self.kinesis_stream = kinesis_stream
        self.streaming_path = f"s3a://{s3_bucket}/streaming"
        self.curated_path = f"s3a://{s3_bucket}/curated"
        
        # Streaming configuration
        self.trigger_interval = "1 minute"
        self.watermark_delay = "10 minutes"
        self.checkpoint_location = f"s3a://{s3_bucket}/checkpoints/streaming"
        
        # Alert thresholds
        self.alert_thresholds = {
            'high_value_transaction': 100000,  # $100k
            'suspicious_frequency': 10,  # 10 transactions per minute
            'large_remittance': 50000,  # $50k
            'failed_transaction_rate': 0.05  # 5% failure rate
        }
    
    def get_transaction_schema(self) -> StructType:
        """Define schema for transaction data"""
        return StructType([
            StructField("transaction_id", StringType(), False),
            StructField("country_code", StringType(), False),
            StructField("loan_id", StringType(), True),
            StructField("transaction_type", StringType(), False),
            StructField("amount", DoubleType(), False),
            StructField("currency", StringType(), False),
            StructField("transaction_date", TimestampType(), False),
            StructField("beneficiary_id", StringType(), True),
            StructField("sector", StringType(), True),
            StructField("status", StringType(), True),
            StructField("source", StringType(), True),
            StructField("processing_timestamp", TimestampType(), True)
        ])
    
    def get_remittance_schema(self) -> StructType:
        """Define schema for remittance data"""
        return StructType([
            StructField("remittance_id", StringType(), False),
            StructField("sender_country", StringType(), False),
            StructField("recipient_country", StringType(), False),
            StructField("amount", DoubleType(), False),
            StructField("currency", StringType(), False),
            StructField("exchange_rate", DoubleType(), True),
            StructField("fees", DoubleType(), True),
            StructField("transaction_date", TimestampType(), False),
            StructField("sender_id", StringType(), True),
            StructField("recipient_id", StringType(), True),
            StructField("status", StringType(), True),
            StructField("processing_timestamp", TimestampType(), True)
        ])
    
    def read_kinesis_stream(self, stream_name: str, schema: StructType) -> DataFrame:
        """Read data from Kinesis stream"""
        logger.info(f"Reading from Kinesis stream: {stream_name}")
        
        df = self.spark.readStream \
            .format("kinesis") \
            .option("streamName", stream_name) \
            .option("region", "us-east-1") \
            .option("initialPosition", "latest") \
            .option("maxOffsetsPerTrigger", 1000) \
            .load()
        
        # Parse JSON data
        parsed_df = df.select(
            from_json(col("data").cast("string"), schema).alias("parsed_data")
        ).select("parsed_data.*")
        
        return parsed_df
    
    def apply_streaming_transformations(self, df: DataFrame, data_type: str) -> DataFrame:
        """Apply transformations to streaming data"""
        logger.info(f"Applying transformations for {data_type} data...")
        
        if data_type == "transactions":
            df = df.withColumn("country_code", upper(trim(col("country_code"))))
            df = df.withColumn("transaction_type", upper(trim(col("transaction_type"))))
            df = df.withColumn("sector", upper(trim(col("sector"))))
            df = df.withColumn("transaction_hash", sha2(col("transaction_id"), 256))
            
            # Add date partitions
            df = df.withColumn("year", year(col("transaction_date")))
            df = df.withColumn("month", month(col("transaction_date")))
            df = df.withColumn("day", dayofmonth(col("transaction_date")))
            
            # Add risk indicators
            df = df.withColumn("high_value_flag", 
                              when(col("amount") > self.alert_thresholds['high_value_transaction'], True)
                              .otherwise(False))
            
        elif data_type == "remittances":
            df = df.withColumn("sender_country", upper(trim(col("sender_country"))))
            df = df.withColumn("recipient_country", upper(trim(col("recipient_country"))))
            df = df.withColumn("remittance_hash", sha2(col("remittance_id"), 256))
            
            # Add date partitions
            df = df.withColumn("year", year(col("transaction_date")))
            df = df.withColumn("month", month(col("transaction_date")))
            df = df.withColumn("day", dayofmonth(col("transaction_date")))
            
            # Add risk indicators
            df = df.withColumn("large_remittance_flag", 
                              when(col("amount") > self.alert_thresholds['large_remittance'], True)
                              .otherwise(False))
            
            # Calculate total amount including fees
            df = df.withColumn("total_amount", 
                              col("amount") + coalesce(col("fees"), lit(0)))
        
        # Add processing timestamp
        df = df.withColumn("processing_timestamp", current_timestamp())
        
        return df
    
    def create_real_time_analytics(self, df: DataFrame, data_type: str) -> DataFrame:
        """Create real-time analytics aggregations"""
        logger.info(f"Creating real-time analytics for {data_type}...")
        
        if data_type == "transactions":
            # Window-based aggregations
            windowed_agg = df.withWatermark("transaction_date", self.watermark_delay) \
                .groupBy(
                    window("transaction_date", "5 minutes", "1 minute"),
                    "country_code",
                    "transaction_type"
                ) \
                .agg(
                    count("*").alias("transaction_count"),
                    spark_sum("amount").alias("total_amount"),
                    avg("amount").alias("avg_amount"),
                    spark_max("amount").alias("max_amount"),
                    spark_min("amount").alias("min_amount")
                )
            
            # Add derived metrics
            analytics_df = windowed_agg.withColumn(
                "transaction_rate_per_minute",
                col("transaction_count") / 5  # 5-minute window
            ).withColumn(
                "high_frequency_flag",
                when(col("transaction_rate_per_minute") > self.alert_thresholds['suspicious_frequency'], True)
                .otherwise(False)
            )
            
        elif data_type == "remittances":
            # Window-based aggregations
            windowed_agg = df.withWatermark("transaction_date", self.watermark_delay) \
                .groupBy(
                    window("transaction_date", "5 minutes", "1 minute"),
                    "sender_country",
                    "recipient_country"
                ) \
                .agg(
                    count("*").alias("remittance_count"),
                    spark_sum("amount").alias("total_amount"),
                    spark_sum("fees").alias("total_fees"),
                    avg("amount").alias("avg_amount"),
                    avg("exchange_rate").alias("avg_exchange_rate")
                )
            
            # Add derived metrics
            analytics_df = windowed_agg.withColumn(
                "remittance_rate_per_minute",
                col("remittance_count") / 5  # 5-minute window
            ).withColumn(
                "fee_percentage",
                (col("total_fees") / col("total_amount")) * 100
            )
        
        return analytics_df
    
    def create_alert_stream(self, df: DataFrame, data_type: str) -> DataFrame:
        """Create alert stream for monitoring"""
        logger.info(f"Creating alert stream for {data_type}...")
        
        if data_type == "transactions":
            alerts_df = df.filter(
                (col("high_value_flag") == True) |
                (col("status") == "FAILED") |
                (col("amount") < 0)
            ).select(
                col("transaction_id"),
                col("country_code"),
                col("amount"),
                col("transaction_type"),
                col("status"),
                col("transaction_date"),
                when(col("high_value_flag") == True, "HIGH_VALUE_TRANSACTION")
                .when(col("status") == "FAILED", "FAILED_TRANSACTION")
                .when(col("amount") < 0, "NEGATIVE_AMOUNT")
                .otherwise("OTHER")
                .alias("alert_type"),
                current_timestamp().alias("alert_timestamp")
            )
            
        elif data_type == "remittances":
            alerts_df = df.filter(
                (col("large_remittance_flag") == True) |
                (col("status") == "FAILED") |
                (col("amount") < 0) |
                (col("exchange_rate").isNull())
            ).select(
                col("remittance_id"),
                col("sender_country"),
                col("recipient_country"),
                col("amount"),
                col("status"),
                col("transaction_date"),
                when(col("large_remittance_flag") == True, "LARGE_REMITTANCE")
                .when(col("status") == "FAILED", "FAILED_REMITTANCE")
                .when(col("amount") < 0, "NEGATIVE_AMOUNT")
                .when(col("exchange_rate").isNull(), "MISSING_EXCHANGE_RATE")
                .otherwise("OTHER")
                .alias("alert_type"),
                current_timestamp().alias("alert_timestamp")
            )
        
        return alerts_df
    
    def write_streaming_data(self, df: DataFrame, output_path: str, 
                           checkpoint_location: str, trigger_interval: str = "1 minute") -> StreamingQuery:
        """Write streaming data to S3"""
        logger.info(f"Writing streaming data to {output_path}")
        
        query = df.writeStream \
            .format("parquet") \
            .option("path", output_path) \
            .option("checkpointLocation", checkpoint_location) \
            .partitionBy("year", "month", "day") \
            .trigger(processingTime=trigger_interval) \
            .outputMode("append") \
            .start()
        
        return query
    
    def write_alert_stream(self, df: DataFrame, output_path: str, 
                          checkpoint_location: str) -> StreamingQuery:
        """Write alert stream to S3"""
        logger.info(f"Writing alert stream to {output_path}")
        
        query = df.writeStream \
            .format("parquet") \
            .option("path", output_path) \
            .option("checkpointLocation", checkpoint_location) \
            .partitionBy("year", "month", "day") \
            .trigger(processingTime="30 seconds") \
            .outputMode("append") \
            .start()
        
        return query
    
    def process_transaction_stream(self) -> List[StreamingQuery]:
        """Process transaction streaming data"""
        logger.info("Starting transaction stream processing...")
        
        # Read transaction stream
        transaction_df = self.read_kinesis_stream(
            f"{self.kinesis_stream}-transactions", 
            self.get_transaction_schema()
        )
        
        # Apply transformations
        transformed_df = self.apply_streaming_transformations(transaction_df, "transactions")
        
        # Create analytics
        analytics_df = self.create_real_time_analytics(transformed_df, "transactions")
        
        # Create alerts
        alerts_df = self.create_alert_stream(transformed_df, "transactions")
        
        # Write streams
        queries = []
        
        # Write transformed data
        transaction_query = self.write_streaming_data(
            transformed_df,
            f"{self.streaming_path}/transactions",
            f"{self.checkpoint_location}/transactions"
        )
        queries.append(transaction_query)
        
        # Write analytics
        analytics_query = self.write_streaming_data(
            analytics_df,
            f"{self.curated_path}/real_time_analytics/transactions",
            f"{self.checkpoint_location}/analytics_transactions"
        )
        queries.append(analytics_query)
        
        # Write alerts
        alerts_query = self.write_alert_stream(
            alerts_df,
            f"{self.streaming_path}/alerts/transactions",
            f"{self.checkpoint_location}/alerts_transactions"
        )
        queries.append(alerts_query)
        
        return queries
    
    def process_remittance_stream(self) -> List[StreamingQuery]:
        """Process remittance streaming data"""
        logger.info("Starting remittance stream processing...")
        
        # Read remittance stream
        remittance_df = self.read_kinesis_stream(
            f"{self.kinesis_stream}-remittances", 
            self.get_remittance_schema()
        )
        
        # Apply transformations
        transformed_df = self.apply_streaming_transformations(remittance_df, "remittances")
        
        # Create analytics
        analytics_df = self.create_real_time_analytics(transformed_df, "remittances")
        
        # Create alerts
        alerts_df = self.create_alert_stream(transformed_df, "remittances")
        
        # Write streams
        queries = []
        
        # Write transformed data
        remittance_query = self.write_streaming_data(
            transformed_df,
            f"{self.streaming_path}/remittances",
            f"{self.checkpoint_location}/remittances"
        )
        queries.append(remittance_query)
        
        # Write analytics
        analytics_query = self.write_streaming_data(
            analytics_df,
            f"{self.curated_path}/real_time_analytics/remittances",
            f"{self.checkpoint_location}/analytics_remittances"
        )
        queries.append(analytics_query)
        
        # Write alerts
        alerts_query = self.write_alert_stream(
            alerts_df,
            f"{self.streaming_path}/alerts/remittances",
            f"{self.checkpoint_location}/alerts_remittances"
        )
        queries.append(alerts_query)
        
        return queries
    
    def run_streaming_pipeline(self):
        """Execute the complete streaming ETL pipeline"""
        logger.info("Starting Regional Bank Streaming ETL Pipeline...")
        
        try:
            # Process transaction stream
            transaction_queries = self.process_transaction_stream()
            
            # Process remittance stream
            remittance_queries = self.process_remittance_stream()
            
            # Combine all queries
            all_queries = transaction_queries + remittance_queries
            
            # Wait for all queries to terminate
            for query in all_queries:
                query.awaitTermination()
                
        except Exception as e:
            logger.error(f"Streaming ETL Pipeline failed: {str(e)}")
            raise


def main():
    """Main function to run the streaming ETL pipeline"""
    
    # Get command line arguments
    if len(sys.argv) != 3:
        print("Usage: streaming_etl.py <s3_bucket> <kinesis_stream_prefix>")
        sys.exit(1)
    
    s3_bucket = sys.argv[1]
    kinesis_stream = sys.argv[2]
    
    # Initialize Spark session
    spark = SparkSession.builder \
        .appName("RegionalBankStreamingETL") \
        .config("spark.sql.streaming.checkpointLocation", f"s3a://{s3_bucket}/checkpoints") \
        .config("spark.sql.streaming.schemaInference", "true") \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
        .config("spark.sql.streaming.statefulOperator.checkCorrectness.enabled", "false") \
        .getOrCreate()
    
    # Set log level
    spark.sparkContext.setLogLevel("WARN")
    
    try:
        # Initialize and run streaming ETL pipeline
        streaming_etl = RegionalBankStreamingETL(spark, s3_bucket, kinesis_stream)
        streaming_etl.run_streaming_pipeline()
        
    finally:
        spark.stop()


if __name__ == "__main__":
    main()

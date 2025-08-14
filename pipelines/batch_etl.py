#!/usr/bin/env python3
"""
Batch ETL Pipeline for Regional Development Bank Data Platform

This script processes batch data from various sources including:
- Economic indicators (GDP, inflation, exchange rates)
- Demographic data (population, education, health)
- Transactional data (loan disbursements, repayments)

Author: Data Engineering Team
Date: 2024
"""

import sys
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from pyspark.sql import SparkSession, DataFrame
from pyspark.sql.functions import (
    col, to_date, year, month, dayofmonth, 
    when, lit, current_timestamp, sha2, 
    regexp_replace, trim, upper, lower
)
from pyspark.sql.types import (
    StructType, StructField, StringType, 
    DoubleType, IntegerType, TimestampType
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RegionalBankETL:
    """
    Main ETL class for processing regional bank data
    """
    
    def __init__(self, spark: SparkSession, s3_bucket: str, processing_date: str):
        self.spark = spark
        self.s3_bucket = s3_bucket
        self.processing_date = processing_date
        self.raw_path = f"s3a://{s3_bucket}/raw"
        self.processed_path = f"s3a://{s3_bucket}/processed"
        self.curated_path = f"s3a://{s3_bucket}/curated"
        
        # Data quality thresholds
        self.quality_thresholds = {
            'null_threshold': 0.1,  # 10% null values allowed
            'duplicate_threshold': 0.05,  # 5% duplicates allowed
            'outlier_threshold': 3.0  # 3 standard deviations for outliers
        }
    
    def read_economic_data(self) -> DataFrame:
        """Read economic indicators data"""
        logger.info("Reading economic indicators data...")
        
        schema = StructType([
            StructField("country_code", StringType(), False),
            StructField("country_name", StringType(), False),
            StructField("indicator_code", StringType(), False),
            StructField("indicator_name", StringType(), False),
            StructField("value", DoubleType(), True),
            StructField("unit", StringType(), True),
            StructField("year", IntegerType(), False),
            StructField("month", IntegerType(), False),
            StructField("source", StringType(), True),
            StructField("last_updated", TimestampType(), True)
        ])
        
        df = self.spark.read.schema(schema).parquet(
            f"{self.raw_path}/economic/date={self.processing_date}"
        )
        
        logger.info(f"Read {df.count()} economic records")
        return df
    
    def read_demographic_data(self) -> DataFrame:
        """Read demographic data"""
        logger.info("Reading demographic data...")
        
        schema = StructType([
            StructField("country_code", StringType(), False),
            StructField("country_name", StringType(), False),
            StructField("population", IntegerType(), True),
            StructField("gdp_per_capita", DoubleType(), True),
            StructField("literacy_rate", DoubleType(), True),
            StructField("life_expectancy", DoubleType(), True),
            StructField("urban_population_pct", DoubleType(), True),
            StructField("year", IntegerType(), False),
            StructField("source", StringType(), True),
            StructField("last_updated", TimestampType(), True)
        ])
        
        df = self.spark.read.schema(schema).parquet(
            f"{self.raw_path}/demographic/date={self.processing_date}"
        )
        
        logger.info(f"Read {df.count()} demographic records")
        return df
    
    def read_transactional_data(self) -> DataFrame:
        """Read transactional data"""
        logger.info("Reading transactional data...")
        
        schema = StructType([
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
            StructField("source", StringType(), True)
        ])
        
        df = self.spark.read.schema(schema).parquet(
            f"{self.raw_path}/transactional/date={self.processing_date}"
        )
        
        logger.info(f"Read {df.count()} transactional records")
        return df
    
    def apply_data_quality_checks(self, df: DataFrame, dataset_name: str) -> DataFrame:
        """Apply data quality checks and validation"""
        logger.info(f"Applying data quality checks for {dataset_name}...")
        
        initial_count = df.count()
        
        # Remove duplicates
        df = df.dropDuplicates()
        
        # Handle null values based on business rules
        if dataset_name == "economic":
            df = df.filter(col("country_code").isNotNull() & 
                          col("indicator_code").isNotNull() &
                          col("value").isNotNull())
        elif dataset_name == "demographic":
            df = df.filter(col("country_code").isNotNull() & 
                          col("population").isNotNull())
        elif dataset_name == "transactional":
            df = df.filter(col("transaction_id").isNotNull() & 
                          col("amount").isNotNull() &
                          col("transaction_date").isNotNull())
        
        # Add data quality metrics
        df = df.withColumn("data_quality_score", lit(1.0))
        df = df.withColumn("processing_timestamp", current_timestamp())
        
        final_count = df.count()
        quality_score = final_count / initial_count if initial_count > 0 else 0
        
        logger.info(f"Data quality check completed for {dataset_name}:")
        logger.info(f"  Initial records: {initial_count}")
        logger.info(f"  Final records: {final_count}")
        logger.info(f"  Quality score: {quality_score:.2%}")
        
        if quality_score < (1 - self.quality_thresholds['null_threshold']):
            logger.warning(f"Data quality below threshold for {dataset_name}")
        
        return df
    
    def transform_economic_data(self, df: DataFrame) -> DataFrame:
        """Transform economic indicators data"""
        logger.info("Transforming economic data...")
        
        df = df.withColumn("country_code", upper(trim(col("country_code"))))
        df = df.withColumn("indicator_code", upper(trim(col("indicator_code"))))
        df = df.withColumn("indicator_category", 
                          when(col("indicator_code").like("GDP%"), "GDP")
                          .when(col("indicator_code").like("INFL%"), "Inflation")
                          .when(col("indicator_code").like("EXCH%"), "Exchange Rate")
                          .when(col("indicator_code").like("INT%"), "Interest Rate")
                          .otherwise("Other"))
        
        # Add year-month partition
        df = df.withColumn("year_month", 
                          col("year") * 100 + col("month"))
        
        return df
    
    def transform_demographic_data(self, df: DataFrame) -> DataFrame:
        """Transform demographic data"""
        logger.info("Transforming demographic data...")
        
        df = df.withColumn("country_code", upper(trim(col("country_code"))))
        
        # Calculate derived metrics
        df = df.withColumn("development_index", 
                          (col("gdp_per_capita") / 1000) * 0.4 +
                          (col("literacy_rate") / 100) * 0.3 +
                          (col("life_expectancy") / 100) * 0.3)
        
        # Add year partition
        df = df.withColumn("year_partition", col("year"))
        
        return df
    
    def transform_transactional_data(self, df: DataFrame) -> DataFrame:
        """Transform transactional data"""
        logger.info("Transforming transactional data...")
        
        df = df.withColumn("country_code", upper(trim(col("country_code"))))
        df = df.withColumn("transaction_type", upper(trim(col("transaction_type"))))
        df = df.withColumn("sector", upper(trim(col("sector"))))
        
        # Add transaction hash for deduplication
        df = df.withColumn("transaction_hash", 
                          sha2(col("transaction_id"), 256))
        
        # Add date partitions
        df = df.withColumn("transaction_date_partition", 
                          to_date(col("transaction_date")))
        df = df.withColumn("year", year(col("transaction_date")))
        df = df.withColumn("month", month(col("transaction_date")))
        df = df.withColumn("day", dayofmonth(col("transaction_date")))
        
        return df
    
    def write_processed_data(self, df: DataFrame, dataset_name: str):
        """Write processed data to S3"""
        logger.info(f"Writing processed {dataset_name} data...")
        
        output_path = f"{self.processed_path}/{dataset_name}/date={self.processing_date}"
        
        df.write.mode("overwrite").partitionBy("year", "month").parquet(output_path)
        
        logger.info(f"Successfully wrote {df.count()} records to {output_path}")
    
    def create_curated_analytics(self):
        """Create curated analytics tables"""
        logger.info("Creating curated analytics tables...")
        
        # Read processed data
        economic_df = self.spark.read.parquet(
            f"{self.processed_path}/economic/date={self.processing_date}"
        )
        demographic_df = self.spark.read.parquet(
            f"{self.processed_path}/demographic/date={self.processing_date}"
        )
        transactional_df = self.spark.read.parquet(
            f"{self.processed_path}/transactional/date={self.processing_date}"
        )
        
        # Create country-level analytics
        country_analytics = self.create_country_analytics(
            economic_df, demographic_df, transactional_df
        )
        
        # Write curated data
        curated_path = f"{self.curated_path}/analytics/date={self.processing_date}"
        country_analytics.write.mode("overwrite").parquet(curated_path)
        
        logger.info("Curated analytics created successfully")
    
    def create_country_analytics(self, economic_df: DataFrame, 
                                demographic_df: DataFrame, 
                                transactional_df: DataFrame) -> DataFrame:
        """Create country-level analytics by joining datasets"""
        
        # Aggregate economic indicators by country
        economic_agg = economic_df.groupBy("country_code", "country_name", "year", "month") \
            .agg({
                "value": "avg",
                "indicator_category": "count"
            }) \
            .withColumnRenamed("avg(value)", "avg_indicator_value") \
            .withColumnRenamed("count(indicator_category)", "indicator_count")
        
        # Aggregate transactional data by country
        transactional_agg = transactional_df.groupBy("country_code", "year", "month") \
            .agg({
                "amount": "sum",
                "transaction_id": "count",
                "transaction_type": "count"
            }) \
            .withColumnRenamed("sum(amount)", "total_transaction_amount") \
            .withColumnRenamed("count(transaction_id)", "transaction_count")
        
        # Join all datasets
        analytics_df = economic_agg.join(
            demographic_df.select("country_code", "population", "gdp_per_capita", "year"),
            ["country_code", "year"],
            "outer"
        ).join(
            transactional_agg,
            ["country_code", "year", "month"],
            "outer"
        )
        
        # Add derived metrics
        analytics_df = analytics_df.withColumn(
            "transaction_per_capita",
            col("transaction_count") / col("population")
        ).withColumn(
            "amount_per_capita",
            col("total_transaction_amount") / col("population")
        )
        
        return analytics_df
    
    def run_pipeline(self):
        """Execute the complete ETL pipeline"""
        logger.info("Starting Regional Bank ETL Pipeline...")
        
        try:
            # Process Economic Data
            economic_df = self.read_economic_data()
            economic_df = self.apply_data_quality_checks(economic_df, "economic")
            economic_df = self.transform_economic_data(economic_df)
            self.write_processed_data(economic_df, "economic")
            
            # Process Demographic Data
            demographic_df = self.read_demographic_data()
            demographic_df = self.apply_data_quality_checks(demographic_df, "demographic")
            demographic_df = self.transform_demographic_data(demographic_df)
            self.write_processed_data(demographic_df, "demographic")
            
            # Process Transactional Data
            transactional_df = self.read_transactional_data()
            transactional_df = self.apply_data_quality_checks(transactional_df, "transactional")
            transactional_df = self.transform_transactional_data(transactional_df)
            self.write_processed_data(transactional_df, "transactional")
            
            # Create Curated Analytics
            self.create_curated_analytics()
            
            logger.info("ETL Pipeline completed successfully!")
            
        except Exception as e:
            logger.error(f"ETL Pipeline failed: {str(e)}")
            raise


def main():
    """Main function to run the ETL pipeline"""
    
    # Get command line arguments
    if len(sys.argv) != 3:
        print("Usage: batch_etl.py <s3_bucket> <processing_date>")
        sys.exit(1)
    
    s3_bucket = sys.argv[1]
    processing_date = sys.argv[2]
    
    # Initialize Spark session
    spark = SparkSession.builder \
        .appName("RegionalBankBatchETL") \
        .config("spark.sql.adaptive.enabled", "true") \
        .config("spark.sql.adaptive.coalescePartitions.enabled", "true") \
        .config("spark.sql.adaptive.skewJoin.enabled", "true") \
        .config("spark.sql.adaptive.localShuffleReader.enabled", "true") \
        .config("spark.sql.parquet.compression", "snappy") \
        .config("spark.sql.parquet.mergeSchema", "false") \
        .getOrCreate()
    
    # Set log level
    spark.sparkContext.setLogLevel("WARN")
    
    try:
        # Initialize and run ETL pipeline
        etl = RegionalBankETL(spark, s3_bucket, processing_date)
        etl.run_pipeline()
        
    finally:
        spark.stop()


if __name__ == "__main__":
    main()

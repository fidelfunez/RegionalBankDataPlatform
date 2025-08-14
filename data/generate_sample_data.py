#!/usr/bin/env python3
"""
Sample Data Generator for Regional Development Bank Data Platform

This script generates realistic sample data for testing the data pipeline:
- Economic indicators
- Demographic data
- Transactional data
- Streaming data

Author: Data Engineering Team
Date: 2024
"""

import pandas as pd
import numpy as np
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import boto3
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class SampleDataGenerator:
    """Generate sample data for the regional bank data platform"""
    
    def __init__(self):
        # Sample countries for regional development bank
        self.countries = [
            {'code': 'BRA', 'name': 'Brazil'},
            {'code': 'ARG', 'name': 'Argentina'},
            {'code': 'CHL', 'name': 'Chile'},
            {'code': 'COL', 'name': 'Colombia'},
            {'code': 'MEX', 'name': 'Mexico'},
            {'code': 'PER', 'name': 'Peru'},
            {'code': 'URY', 'name': 'Uruguay'},
            {'code': 'ECU', 'name': 'Ecuador'},
            {'code': 'BOL', 'name': 'Bolivia'},
            {'code': 'PRY', 'name': 'Paraguay'}
        ]
        
        # Economic indicators
        self.economic_indicators = [
            {'code': 'GDP_CURRENT_USD', 'name': 'GDP (current US$)', 'unit': 'USD'},
            {'code': 'GDP_GROWTH_ANNUAL', 'name': 'GDP growth (annual %)', 'unit': 'Percent'},
            {'code': 'INFLATION_CONSUMER_PRICES', 'name': 'Inflation, consumer prices (annual %)', 'unit': 'Percent'},
            {'code': 'EXCHANGE_RATE_USD', 'name': 'Official exchange rate (LCU per US$, period average)', 'unit': 'LCU per USD'},
            {'code': 'INTEREST_RATE_REAL', 'name': 'Real interest rate (%)', 'unit': 'Percent'},
            {'code': 'UNEMPLOYMENT_TOTAL', 'name': 'Unemployment, total (% of total labor force)', 'unit': 'Percent'}
        ]
        
        # Transaction types
        self.transaction_types = [
            'DISBURSEMENT',
            'REPAYMENT', 
            'INTEREST',
            'FEE',
            'REFUND',
            'ADJUSTMENT'
        ]
        
        # Sectors
        self.sectors = [
            'AGRICULTURE',
            'EDUCATION',
            'HEALTH',
            'INFRASTRUCTURE',
            'SMALL_BUSINESS',
            'ENERGY',
            'WATER_SANITATION',
            'TRANSPORTATION'
        ]
        
        # Currencies
        self.currencies = ['USD', 'EUR', 'BRL', 'ARS', 'CLP', 'COP', 'MXN', 'PEN']
    
    def generate_economic_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Generate economic indicators data"""
        logger.info("Generating economic indicators data...")
        
        data = []
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        current = start
        while current <= end:
            for country in self.countries:
                for indicator in self.economic_indicators:
                    # Generate realistic values based on indicator type
                    if 'GDP' in indicator['code']:
                        if 'CURRENT' in indicator['code']:
                            value = random.uniform(100000000000, 2000000000000)  # $100B - $2T
                        else:
                            value = random.uniform(-5, 10)  # -5% to 10% growth
                    elif 'INFLATION' in indicator['code']:
                        value = random.uniform(0, 50)  # 0% to 50% inflation
                    elif 'EXCHANGE' in indicator['code']:
                        value = random.uniform(1, 100)  # 1-100 local currency per USD
                    elif 'INTEREST' in indicator['code']:
                        value = random.uniform(-10, 20)  # -10% to 20% interest rate
                    elif 'UNEMPLOYMENT' in indicator['code']:
                        value = random.uniform(3, 25)  # 3% to 25% unemployment
                    else:
                        value = random.uniform(0, 100)
                    
                    data.append({
                        'country_code': country['code'],
                        'country_name': country['name'],
                        'indicator_code': indicator['code'],
                        'indicator_name': indicator['name'],
                        'value': round(value, 4),
                        'unit': indicator['unit'],
                        'year': current.year,
                        'month': current.month,
                        'source': 'World Bank',
                        'last_updated': current
                    })
            
            # Move to next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)
        
        df = pd.DataFrame(data)
        logger.info(f"Generated {len(df)} economic records")
        return df
    
    def generate_demographic_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Generate demographic data"""
        logger.info("Generating demographic data...")
        
        data = []
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        current = start
        while current <= end:
            for country in self.countries:
                # Generate realistic demographic data
                population = random.randint(5000000, 200000000)  # 5M to 200M
                gdp_per_capita = random.uniform(1000, 50000)  # $1K to $50K
                literacy_rate = random.uniform(70, 99)  # 70% to 99%
                life_expectancy = random.uniform(60, 85)  # 60 to 85 years
                urban_population_pct = random.uniform(30, 90)  # 30% to 90%
                
                data.append({
                    'country_code': country['code'],
                    'country_name': country['name'],
                    'population': population,
                    'gdp_per_capita': round(gdp_per_capita, 2),
                    'literacy_rate': round(literacy_rate, 2),
                    'life_expectancy': round(life_expectancy, 2),
                    'urban_population_pct': round(urban_population_pct, 2),
                    'year': current.year,
                    'source': 'UN Statistics',
                    'last_updated': current
                })
            
            # Move to next year
            current = current.replace(year=current.year + 1)
        
        df = pd.DataFrame(data)
        logger.info(f"Generated {len(df)} demographic records")
        return df
    
    def generate_transaction_data(self, start_date: str, end_date: str, num_transactions: int = 10000) -> pd.DataFrame:
        """Generate transactional data"""
        logger.info("Generating transactional data...")
        
        data = []
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        for _ in range(num_transactions):
            # Random transaction date
            transaction_date = start + timedelta(
                days=random.randint(0, (end - start).days)
            )
            
            country = random.choice(self.countries)
            transaction_type = random.choice(self.transaction_types)
            sector = random.choice(self.sectors)
            currency = random.choice(self.currencies)
            
            # Generate realistic amounts based on transaction type
            if transaction_type == 'DISBURSEMENT':
                amount = random.uniform(1000, 1000000)  # $1K to $1M
            elif transaction_type == 'REPAYMENT':
                amount = random.uniform(100, 500000)  # $100 to $500K
            elif transaction_type in ['INTEREST', 'FEE']:
                amount = random.uniform(10, 10000)  # $10 to $10K
            else:
                amount = random.uniform(1, 100000)  # $1 to $100K
            
            # Generate loan and beneficiary IDs
            loan_id = f"LOAN_{random.randint(100000, 999999)}"
            beneficiary_id = f"BEN_{random.randint(100000, 999999)}"
            
            # Transaction status
            status = random.choices(
                ['SUCCESS', 'FAILED', 'PENDING'],
                weights=[0.95, 0.03, 0.02]
            )[0]
            
            data.append({
                'transaction_id': f"TXN_{random.randint(100000000, 999999999)}",
                'country_code': country['code'],
                'loan_id': loan_id,
                'transaction_type': transaction_type,
                'amount': round(amount, 2),
                'currency': currency,
                'transaction_date': transaction_date,
                'beneficiary_id': beneficiary_id,
                'sector': sector,
                'status': status,
                'source': 'Core Banking System'
            })
        
        df = pd.DataFrame(data)
        logger.info(f"Generated {len(df)} transaction records")
        return df
    
    def generate_streaming_data(self, num_records: int = 1000) -> List[Dict[str, Any]]:
        """Generate streaming data for Kinesis"""
        logger.info("Generating streaming data...")
        
        data = []
        
        for _ in range(num_records):
            # Generate transaction streaming data
            transaction_data = {
                'transaction_id': f"TXN_{random.randint(100000000, 999999999)}",
                'country_code': random.choice(self.countries)['code'],
                'loan_id': f"LOAN_{random.randint(100000, 999999)}",
                'transaction_type': random.choice(self.transaction_types),
                'amount': round(random.uniform(100, 100000), 2),
                'currency': random.choice(self.currencies),
                'transaction_date': datetime.now().isoformat(),
                'beneficiary_id': f"BEN_{random.randint(100000, 999999)}",
                'sector': random.choice(self.sectors),
                'status': random.choice(['SUCCESS', 'FAILED', 'PENDING']),
                'source': 'Real-time System'
            }
            
            # Generate remittance streaming data
            remittance_data = {
                'remittance_id': f"REM_{random.randint(100000000, 999999999)}",
                'sender_country': random.choice(self.countries)['code'],
                'recipient_country': random.choice(self.countries)['code'],
                'amount': round(random.uniform(50, 50000), 2),
                'currency': random.choice(self.currencies),
                'exchange_rate': round(random.uniform(0.5, 2.0), 4),
                'fees': round(random.uniform(1, 100), 2),
                'transaction_date': datetime.now().isoformat(),
                'sender_id': f"SND_{random.randint(100000, 999999)}",
                'recipient_id': f"RCP_{random.randint(100000, 999999)}",
                'status': random.choice(['SUCCESS', 'FAILED', 'PENDING']),
                'source': 'Remittance System'
            }
            
            data.extend([
                {'type': 'transaction', 'data': transaction_data},
                {'type': 'remittance', 'data': remittance_data}
            ])
        
        logger.info(f"Generated {len(data)} streaming records")
        return data
    
    def save_to_s3(self, df: pd.DataFrame, bucket: str, key: str, format: str = 'parquet'):
        """Save data to S3"""
        logger.info(f"Saving data to s3://{bucket}/{key}")
        
        s3_client = boto3.client('s3')
        
        if format == 'parquet':
            # Save as parquet
            parquet_buffer = df.to_parquet(index=False)
            s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=parquet_buffer
            )
        elif format == 'csv':
            # Save as CSV
            csv_buffer = df.to_csv(index=False)
            s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=csv_buffer
            )
        elif format == 'json':
            # Save as JSON
            json_buffer = df.to_json(orient='records', date_format='iso')
            s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=json_buffer
            )
    
    def generate_all_sample_data(self, bucket: str, date: str = None):
        """Generate all sample data and save to S3"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"Generating sample data for {date}")
        
        # Generate economic data
        economic_df = self.generate_economic_data('2020-01-01', date)
        self.save_to_s3(
            economic_df, 
            bucket, 
            f'raw/economic/date={date}/economic_indicators.parquet'
        )
        
        # Generate demographic data
        demographic_df = self.generate_demographic_data('2020-01-01', date)
        self.save_to_s3(
            demographic_df, 
            bucket, 
            f'raw/demographic/date={date}/demographic_data.parquet'
        )
        
        # Generate transaction data
        transaction_df = self.generate_transaction_data('2020-01-01', date, 50000)
        self.save_to_s3(
            transaction_df, 
            bucket, 
            f'raw/transactional/date={date}/transactions.parquet'
        )
        
        # Generate streaming data
        streaming_data = self.generate_streaming_data(1000)
        
        # Save streaming data as JSON
        s3_client = boto3.client('s3')
        for i, record in enumerate(streaming_data):
            key = f'streaming/{record["type"]}/date={date}/record_{i:06d}.json'
            s3_client.put_object(
                Bucket=bucket,
                Key=key,
                Body=json.dumps(record)
            )
        
        logger.info("Sample data generation completed!")


def main():
    """Main function to generate sample data"""
    
    # Initialize generator
    generator = SampleDataGenerator()
    
    # Generate data for the last 30 days
    end_date = datetime.now()
    start_date = end_date - timedelta(days=30)
    
    # S3 bucket (replace with your bucket name)
    bucket = "dev-regional-bank-data-lake"
    
    # Generate data for each day
    current_date = start_date
    while current_date <= end_date:
        date_str = current_date.strftime('%Y-%m-%d')
        print(f"Generating data for {date_str}")
        
        try:
            generator.generate_all_sample_data(bucket, date_str)
        except Exception as e:
            print(f"Error generating data for {date_str}: {e}")
        
        current_date += timedelta(days=1)


if __name__ == "__main__":
    main()

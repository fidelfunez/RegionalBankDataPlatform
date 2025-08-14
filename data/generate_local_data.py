#!/usr/bin/env python3
"""
Local Sample Data Generator for Regional Development Bank Data Platform
"""
import pandas as pd
import numpy as np
import json
import random
from datetime import datetime, timedelta
from typing import List, Dict, Any
import logging
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LocalSampleDataGenerator:
    def __init__(self):
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
        
        self.economic_indicators = [
            {'code': 'GDP_CURRENT_USD', 'name': 'GDP (current US$)', 'unit': 'USD'},
            {'code': 'INFLATION_CPI', 'name': 'Inflation, consumer prices', 'unit': 'Percent'},
            {'code': 'EXCHANGE_RATE', 'name': 'Official exchange rate', 'unit': 'Local Currency per USD'},
            {'code': 'INTEREST_RATE', 'name': 'Interest rate', 'unit': 'Percent'},
            {'code': 'UNEMPLOYMENT', 'name': 'Unemployment rate', 'unit': 'Percent'},
            {'code': 'EXPORTS', 'name': 'Exports of goods and services', 'unit': 'USD'},
            {'code': 'IMPORTS', 'name': 'Imports of goods and services', 'unit': 'USD'},
            {'code': 'FDI', 'name': 'Foreign direct investment', 'unit': 'USD'}
        ]
        
        self.transaction_types = [
            'DISBURSEMENT', 'REPAYMENT', 'INTEREST', 'FEE', 'REFUND', 'ADJUSTMENT'
        ]
        
        self.sectors = [
            'AGRICULTURE', 'EDUCATION', 'HEALTH', 'INFRASTRUCTURE', 
            'SMALL_BUSINESS', 'ENERGY', 'WATER_SANITATION', 'TRANSPORTATION'
        ]
        
        self.currencies = ['USD', 'EUR', 'BRL', 'ARS', 'CLP', 'COP', 'MXN', 'PEN']

    def generate_economic_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Generate economic indicators data"""
        logger.info("Generating economic indicators data...")
        
        data = []
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        for country in self.countries:
            for indicator in self.economic_indicators:
                current_date = start
                while current_date <= end:
                    # Generate realistic economic data
                    if indicator['code'] == 'GDP_CURRENT_USD':
                        base_value = random.uniform(100000000000, 2000000000000)
                        value = base_value * (1 + random.uniform(-0.1, 0.15))
                    elif indicator['code'] == 'INFLATION_CPI':
                        value = random.uniform(1.0, 15.0)
                    elif indicator['code'] == 'EXCHANGE_RATE':
                        value = random.uniform(0.5, 5.0)
                    elif indicator['code'] == 'INTEREST_RATE':
                        value = random.uniform(2.0, 25.0)
                    elif indicator['code'] == 'UNEMPLOYMENT':
                        value = random.uniform(3.0, 20.0)
                    else:
                        value = random.uniform(1000000, 100000000)
                    
                    data.append({
                        'country_code': country['code'],
                        'country_name': country['name'],
                        'indicator_code': indicator['code'],
                        'indicator_name': indicator['name'],
                        'value': round(value, 4),
                        'unit': indicator['unit'],
                        'year': current_date.year,
                        'month': current_date.month,
                        'source': 'World Bank API',
                        'last_updated': current_date.isoformat()
                    })
                    
                    current_date += timedelta(days=30)
        
        df = pd.DataFrame(data)
        logger.info(f"Generated {len(df)} economic records")
        return df

    def generate_demographic_data(self, start_date: str, end_date: str) -> pd.DataFrame:
        """Generate demographic data"""
        logger.info("Generating demographic data...")
        
        data = []
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        for country in self.countries:
            current_date = start
            while current_date <= end:
                # Generate realistic demographic data
                population = random.randint(5000000, 220000000)
                gdp_per_capita = random.uniform(1000, 50000)
                literacy_rate = random.uniform(70, 99)
                life_expectancy = random.uniform(60, 85)
                urban_population_pct = random.uniform(30, 90)
                
                data.append({
                    'country_code': country['code'],
                    'country_name': country['name'],
                    'population': population,
                    'gdp_per_capita': round(gdp_per_capita, 2),
                    'literacy_rate': round(literacy_rate, 2),
                    'life_expectancy': round(life_expectancy, 2),
                    'urban_population_pct': round(urban_population_pct, 2),
                    'year': current_date.year,
                    'source': 'UN Statistics',
                    'last_updated': current_date.isoformat()
                })
                
                current_date += timedelta(days=365)
        
        df = pd.DataFrame(data)
        logger.info(f"Generated {len(df)} demographic records")
        return df

    def generate_transaction_data(self, start_date: str, end_date: str, num_transactions: int = 10000) -> pd.DataFrame:
        """Generate transactional data"""
        logger.info("Generating transaction data...")
        
        data = []
        start = datetime.strptime(start_date, '%Y-%m-%d')
        end = datetime.strptime(end_date, '%Y-%m-%d')
        
        for _ in range(num_transactions):
            # Random transaction date
            days_between = (end - start).days
            random_days = random.randint(0, days_between)
            transaction_date = start + timedelta(days=random_days)
            
            # Random country and transaction details
            country = random.choice(self.countries)
            transaction_type = random.choice(self.transaction_types)
            sector = random.choice(self.sectors)
            currency = random.choice(self.currencies)
            
            # Generate realistic amounts based on transaction type
            if transaction_type == 'DISBURSEMENT':
                amount = random.uniform(10000, 1000000)
            elif transaction_type == 'REPAYMENT':
                amount = random.uniform(5000, 500000)
            else:
                amount = random.uniform(100, 10000)
            
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
                'transaction_date': transaction_date.strftime('%Y-%m-%d'),
                'beneficiary_id': beneficiary_id,
                'sector': sector,
                'status': status,
                'source': 'Core Banking System'
            })
        
        df = pd.DataFrame(data)
        logger.info(f"Generated {len(df)} transaction records")
        return df

    def save_to_local(self, df: pd.DataFrame, filepath: str, format: str = 'parquet'):
        """Save data to local file"""
        logger.info(f"Saving data to {filepath}")
        
        # Create directory if it doesn't exist
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        if format == 'parquet':
            df.to_parquet(filepath, index=False)
        elif format == 'csv':
            df.to_csv(filepath, index=False)
        elif format == 'json':
            df.to_json(filepath, orient='records', date_format='iso')
        
        logger.info(f"Successfully saved {len(df)} records to {filepath}")

    def generate_all_sample_data(self, output_dir: str = "sample_data", date: str = None):
        """Generate all sample data and save locally"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        logger.info(f"Generating sample data for {date}")
        
        # Generate economic data
        economic_df = self.generate_economic_data('2020-01-01', date)
        self.save_to_local(economic_df, f"{output_dir}/economic/economic_indicators_{date}.parquet")
        
        # Generate demographic data
        demographic_df = self.generate_demographic_data('2020-01-01', date)
        self.save_to_local(demographic_df, f"{output_dir}/demographic/demographic_data_{date}.parquet")
        
        # Generate transaction data
        transaction_df = self.generate_transaction_data('2020-01-01', date, 50000)
        self.save_to_local(transaction_df, f"{output_dir}/transactional/transactions_{date}.parquet")
        
        logger.info("Sample data generation completed!")

def main():
    generator = LocalSampleDataGenerator()
    output_dir = "sample_data"
    
    # Generate data for today
    today = datetime.now().strftime('%Y-%m-%d')
    print(f"Generating data for {today}")
    
    try:
        generator.generate_all_sample_data(output_dir, today)
        print(f"✅ Successfully generated sample data in {output_dir}/")
        print(f"📁 Files created:")
        print(f"   - {output_dir}/economic/economic_indicators_{today}.parquet")
        print(f"   - {output_dir}/demographic/demographic_data_{today}.parquet")
        print(f"   - {output_dir}/transactional/transactions_{today}.parquet")
    except Exception as e:
        print(f"❌ Error generating data: {e}")

if __name__ == "__main__":
    main()

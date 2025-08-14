#!/usr/bin/env python3
"""
Regional Development Bank Data Platform - Demo Pipeline
This script demonstrates the complete data pipeline working locally
"""
import pandas as pd
import sqlite3
import json
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_sample_data():
    """Load the generated sample data"""
    logger.info("Loading sample data...")
    
    try:
        # Load economic data
        economic_df = pd.read_parquet('sample_data/economic/economic_indicators_2025-08-13.parquet')
        logger.info(f"✅ Loaded {len(economic_df)} economic records")
        
        # Load demographic data
        demographic_df = pd.read_parquet('sample_data/demographic/demographic_data_2025-08-13.parquet')
        logger.info(f"✅ Loaded {len(demographic_df)} demographic records")
        
        # Load transaction data
        transaction_df = pd.read_parquet('sample_data/transactional/transactions_2025-08-13.parquet')
        logger.info(f"✅ Loaded {len(transaction_df)} transaction records")
        
        return economic_df, demographic_df, transaction_df
    
    except Exception as e:
        logger.error(f"❌ Error loading sample data: {e}")
        return None, None, None

def create_database_schema():
    """Create the database schema"""
    logger.info("Creating database schema...")
    
    conn = sqlite3.connect('regional_bank.db')
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS economic_indicators (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country_code TEXT,
            country_name TEXT,
            indicator_code TEXT,
            indicator_name TEXT,
            value REAL,
            unit TEXT,
            year INTEGER,
            month INTEGER,
            source TEXT,
            last_updated TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS demographic_data (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country_code TEXT,
            country_name TEXT,
            population INTEGER,
            gdp_per_capita REAL,
            literacy_rate REAL,
            life_expectancy REAL,
            urban_population_pct REAL,
            year INTEGER,
            source TEXT,
            last_updated TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            transaction_id TEXT,
            country_code TEXT,
            loan_id TEXT,
            transaction_type TEXT,
            amount REAL,
            currency TEXT,
            transaction_date TEXT,
            beneficiary_id TEXT,
            sector TEXT,
            status TEXT,
            source TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS regional_analytics (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            country_code TEXT,
            country_name TEXT,
            month_date TEXT,
            total_transactions INTEGER,
            total_amount REAL,
            avg_transaction_amount REAL,
            disbursement_amount REAL,
            repayment_amount REAL,
            failed_transactions INTEGER,
            population INTEGER,
            gdp_per_capita REAL,
            created_at TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("✅ Database schema created successfully!")

def load_data_to_database(economic_df, demographic_df, transaction_df):
    """Load data into the database"""
    logger.info("Loading data into database...")
    
    conn = sqlite3.connect('regional_bank.db')
    
    # Load economic data
    economic_df.to_sql('economic_indicators', conn, if_exists='replace', index=False)
    logger.info(f"✅ Loaded {len(economic_df)} economic records to database")
    
    # Load demographic data
    demographic_df.to_sql('demographic_data', conn, if_exists='replace', index=False)
    logger.info(f"✅ Loaded {len(demographic_df)} demographic records to database")
    
    # Load transaction data
    transaction_df.to_sql('transactions', conn, if_exists='replace', index=False)
    logger.info(f"✅ Loaded {len(transaction_df)} transaction records to database")
    
    conn.close()

def create_analytics():
    """Create analytics by joining the data"""
    logger.info("Creating analytics...")
    
    conn = sqlite3.connect('regional_bank.db')
    
    # Create analytics query
    analytics_query = '''
        WITH country_transactions AS (
            SELECT 
                t.country_code,
                COUNT(*) as total_transactions,
                SUM(t.amount) as total_amount,
                AVG(t.amount) as avg_transaction_amount,
                SUM(CASE WHEN t.transaction_type = 'DISBURSEMENT' THEN t.amount ELSE 0 END) as disbursement_amount,
                SUM(CASE WHEN t.transaction_type = 'REPAYMENT' THEN t.amount ELSE 0 END) as repayment_amount,
                COUNT(CASE WHEN t.status = 'FAILED' THEN 1 END) as failed_transactions,
                strftime('%Y-%m', t.transaction_date) as month_date
            FROM transactions t
            GROUP BY t.country_code, strftime('%Y-%m', t.transaction_date)
        ),
        country_demographics AS (
            SELECT 
                d.country_code,
                d.country_name,
                d.population,
                d.gdp_per_capita
            FROM demographic_data d
            WHERE d.year = (SELECT MAX(year) FROM demographic_data)
        )
        SELECT 
            ct.country_code,
            cd.country_name,
            ct.month_date,
            ct.total_transactions,
            ct.total_amount,
            ct.avg_transaction_amount,
            ct.disbursement_amount,
            ct.repayment_amount,
            ct.failed_transactions,
            cd.population,
            cd.gdp_per_capita,
            datetime('now') as created_at
        FROM country_transactions ct
        LEFT JOIN country_demographics cd ON ct.country_code = cd.country_code
        ORDER BY ct.country_code, ct.month_date
    '''
    
    analytics_df = pd.read_sql_query(analytics_query, conn)
    analytics_df.to_sql('regional_analytics', conn, if_exists='replace', index=False)
    
    logger.info(f"✅ Created {len(analytics_df)} analytics records")
    
    # Show some sample analytics
    print("\n📊 Sample Analytics:")
    print(analytics_df.head(10).to_string(index=False))
    
    conn.close()

def generate_insights():
    """Generate insights from the data"""
    logger.info("Generating insights...")
    
    conn = sqlite3.connect('regional_bank.db')
    
    insights = []
    
    # Top countries by transaction volume
    top_countries_query = '''
        SELECT 
            country_code,
            country_name,
            SUM(total_transactions) as total_transactions,
            SUM(total_amount) as total_amount
        FROM regional_analytics
        GROUP BY country_code, country_name
        ORDER BY total_transactions DESC
        LIMIT 5
    '''
    
    top_countries = pd.read_sql_query(top_countries_query, conn)
    insights.append({
        'insight': 'Top 5 Countries by Transaction Volume',
        'data': top_countries.to_dict('records')
    })
    
    # Transaction success rate
    success_rate_query = '''
        SELECT 
            COUNT(*) as total_transactions,
            COUNT(CASE WHEN status = 'SUCCESS' THEN 1 END) as successful_transactions,
            ROUND(COUNT(CASE WHEN status = 'SUCCESS' THEN 1 END) * 100.0 / COUNT(*), 2) as success_rate
        FROM transactions
    '''
    
    success_rate = pd.read_sql_query(success_rate_query, conn)
    insights.append({
        'insight': 'Overall Transaction Success Rate',
        'data': success_rate.to_dict('records')
    })
    
    # Average transaction amount by sector
    sector_analysis_query = '''
        SELECT 
            sector,
            COUNT(*) as transaction_count,
            AVG(amount) as avg_amount,
            SUM(amount) as total_amount
        FROM transactions
        GROUP BY sector
        ORDER BY total_amount DESC
    '''
    
    sector_analysis = pd.read_sql_query(sector_analysis_query, conn)
    insights.append({
        'insight': 'Transaction Analysis by Sector',
        'data': sector_analysis.to_dict('records')
    })
    
    conn.close()
    
    # Display insights
    print("\n🔍 Key Insights:")
    for insight in insights:
        print(f"\n{insight['insight']}:")
        for record in insight['data']:
            print(f"  {record}")
    
    return insights

def main():
    """Main demonstration function"""
    print("🚀 Regional Development Bank Data Platform - Demo")
    print("=" * 60)
    
    # Step 1: Load sample data
    economic_df, demographic_df, transaction_df = load_sample_data()
    if economic_df is None:
        print("❌ Failed to load sample data. Please run the data generation first.")
        return
    
    # Step 2: Create database schema
    create_database_schema()
    
    # Step 3: Load data into database
    load_data_to_database(economic_df, demographic_df, transaction_df)
    
    # Step 4: Create analytics
    create_analytics()
    
    # Step 5: Generate insights
    insights = generate_insights()
    
    print("\n" + "=" * 60)
    print("✅ Demo completed successfully!")
    print("\n📁 Files created:")
    print("   - regional_bank.db (SQLite database)")
    print("   - sample_data/ (Sample data files)")
    
    print("\n🎯 What we demonstrated:")
    print("   ✅ Data generation (economic, demographic, transactional)")
    print("   ✅ Data storage (SQLite database)")
    print("   ✅ Data transformation (analytics creation)")
    print("   ✅ Business insights (KPIs and metrics)")
    
    print("\n🔧 Next steps for production:")
    print("   - Deploy to AWS with Terraform")
    print("   - Use Redshift for data warehouse")
    print("   - Set up Airflow for orchestration")
    print("   - Implement real-time streaming with Kinesis")
    print("   - Add monitoring and alerting")

if __name__ == "__main__":
    main()

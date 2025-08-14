#!/usr/bin/env python3
"""
Regional Development Bank Data Platform Setup Script

This script automates the complete setup of the data platform including:
- Infrastructure deployment with Terraform
- Data pipeline configuration
- Monitoring setup
- Sample data generation

Author: Data Engineering Team
Date: 2024
"""

import os
import sys
import subprocess
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DataPlatformSetup:
    """Setup class for the regional bank data platform"""
    
    def __init__(self, environment: str = 'dev', region: str = 'us-east-1'):
        self.environment = environment
        self.region = region
        self.project_root = Path(__file__).parent.parent
        
    def check_prerequisites(self) -> bool:
        """Check if all prerequisites are installed"""
        logger.info("Checking prerequisites...")
        
        required_tools = {
            'terraform': 'terraform --version',
            'aws': 'aws --version',
            'docker': 'docker --version',
            'docker-compose': 'docker-compose --version',
            'python': 'python --version',
            'pip': 'pip --version'
        }
        
        missing_tools = []
        
        for tool, command in required_tools.items():
            try:
                result = subprocess.run(
                    command.split(), 
                    capture_output=True, 
                    text=True, 
                    check=True
                )
                logger.info(f"✓ {tool}: {result.stdout.strip()}")
            except (subprocess.CalledProcessError, FileNotFoundError):
                logger.error(f"✗ {tool}: Not found")
                missing_tools.append(tool)
        
        if missing_tools:
            logger.error(f"Missing required tools: {', '.join(missing_tools)}")
            logger.error("Please install the missing tools and try again.")
            return False
        
        return True
    
    def setup_aws_credentials(self) -> bool:
        """Setup AWS credentials"""
        logger.info("Setting up AWS credentials...")
        
        # Check if AWS credentials are configured
        try:
            result = subprocess.run(
                ['aws', 'sts', 'get-caller-identity'],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info("✓ AWS credentials are configured")
            return True
        except subprocess.CalledProcessError:
            logger.warning("AWS credentials not configured. Please run 'aws configure'")
            return False
    
    def deploy_infrastructure(self) -> bool:
        """Deploy infrastructure using Terraform"""
        logger.info("Deploying infrastructure with Terraform...")
        
        terraform_dir = self.project_root / 'terraform'
        
        try:
            # Initialize Terraform
            logger.info("Initializing Terraform...")
            subprocess.run(
                ['terraform', 'init'],
                cwd=terraform_dir,
                check=True
            )
            
            # Plan Terraform deployment
            logger.info("Planning Terraform deployment...")
            subprocess.run(
                ['terraform', 'plan', '-var', f'environment={self.environment}'],
                cwd=terraform_dir,
                check=True
            )
            
            # Apply Terraform deployment
            logger.info("Applying Terraform deployment...")
            subprocess.run(
                ['terraform', 'apply', '-var', f'environment={self.environment}', '-auto-approve'],
                cwd=terraform_dir,
                check=True
            )
            
            logger.info("✓ Infrastructure deployed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"✗ Infrastructure deployment failed: {e}")
            return False
    
    def setup_data_pipeline(self) -> bool:
        """Setup data pipeline components"""
        logger.info("Setting up data pipeline...")
        
        try:
            # Install Python dependencies
            logger.info("Installing Python dependencies...")
            subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
                cwd=self.project_root,
                check=True
            )
            
            # Upload pipeline scripts to S3
            logger.info("Uploading pipeline scripts to S3...")
            s3_bucket = f"{self.environment}-regional-bank-data-lake"
            
            # Upload batch ETL script
            subprocess.run([
                'aws', 's3', 'cp',
                str(self.project_root / 'pipelines' / 'batch_etl.py'),
                f's3://{s3_bucket}/scripts/batch_etl.py'
            ], check=True)
            
            # Upload streaming ETL script
            subprocess.run([
                'aws', 's3', 'cp',
                str(self.project_root / 'pipelines' / 'streaming_etl.py'),
                f's3://{s3_bucket}/scripts/streaming_etl.py'
            ], check=True)
            
            logger.info("✓ Data pipeline setup completed")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"✗ Data pipeline setup failed: {e}")
            return False
    
    def setup_monitoring(self) -> bool:
        """Setup monitoring and alerting"""
        logger.info("Setting up monitoring and alerting...")
        
        try:
            # Run monitoring setup script
            monitoring_script = self.project_root / 'monitoring' / 'cloudwatch_alarms.py'
            subprocess.run([sys.executable, str(monitoring_script)], check=True)
            
            logger.info("✓ Monitoring setup completed")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"✗ Monitoring setup failed: {e}")
            return False
    
    def setup_airflow(self) -> bool:
        """Setup Apache Airflow"""
        logger.info("Setting up Apache Airflow...")
        
        airflow_dir = self.project_root / 'airflow'
        
        try:
            # Set Airflow UID for Linux
            if os.name == 'posix':
                os.environ['AIRFLOW_UID'] = str(os.getuid())
            
            # Start Airflow services
            logger.info("Starting Airflow services...")
            subprocess.run(
                ['docker-compose', 'up', '-d'],
                cwd=airflow_dir,
                check=True
            )
            
            # Wait for Airflow to be ready
            logger.info("Waiting for Airflow to be ready...")
            import time
            time.sleep(30)
            
            logger.info("✓ Airflow setup completed")
            logger.info("Airflow UI available at: http://localhost:8080")
            logger.info("Username: admin, Password: admin")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"✗ Airflow setup failed: {e}")
            return False
    
    def generate_sample_data(self) -> bool:
        """Generate sample data for testing"""
        logger.info("Generating sample data...")
        
        try:
            # Run sample data generator
            data_script = self.project_root / 'data' / 'generate_sample_data.py'
            subprocess.run([sys.executable, str(data_script)], check=True)
            
            logger.info("✓ Sample data generation completed")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"✗ Sample data generation failed: {e}")
            return False
    
    def setup_dbt(self) -> bool:
        """Setup dbt project"""
        logger.info("Setting up dbt project...")
        
        dbt_dir = self.project_root / 'dbt'
        
        try:
            # Install dbt dependencies
            subprocess.run(['dbt', 'deps'], cwd=dbt_dir, check=True)
            
            # Run dbt models
            subprocess.run(['dbt', 'run'], cwd=dbt_dir, check=True)
            
            # Run dbt tests
            subprocess.run(['dbt', 'test'], cwd=dbt_dir, check=True)
            
            # Generate dbt docs
            subprocess.run(['dbt', 'docs', 'generate'], cwd=dbt_dir, check=True)
            
            logger.info("✓ dbt setup completed")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.error(f"✗ dbt setup failed: {e}")
            return False
    
    def create_documentation(self) -> bool:
        """Create project documentation"""
        logger.info("Creating project documentation...")
        
        try:
            # Create architecture diagram
            self.create_architecture_diagram()
            
            # Create runbooks
            self.create_runbooks()
            
            logger.info("✓ Documentation created")
            return True
            
        except Exception as e:
            logger.error(f"✗ Documentation creation failed: {e}")
            return False
    
    def create_architecture_diagram(self):
        """Create architecture diagram"""
        docs_dir = self.project_root / 'docs'
        docs_dir.mkdir(exist_ok=True)
        
        # Create a simple text-based architecture diagram
        diagram_content = """
# Regional Development Bank Data Platform Architecture

## Data Flow
```
Data Sources → S3 Raw → Glue ETL → S3 Processed → Redshift → dbt → Analytics
     ↓              ↓         ↓           ↓          ↓       ↓        ↓
  Batch CSV    Parquet    Spark      Parquet    Tables   Models   Dashboards
  Streaming    JSON       Python     Parquet    Views    Tests    Reports
```

## Components
- **Data Sources**: Economic indicators, demographic data, transactions
- **S3 Data Lake**: Raw, processed, curated, and streaming data layers
- **AWS Glue**: ETL jobs for batch and streaming processing
- **Amazon Redshift**: Data warehouse for analytics
- **dbt**: Data transformation and modeling
- **Apache Airflow**: Pipeline orchestration
- **CloudWatch**: Monitoring and alerting
- **OpenMetadata**: Data catalog and governance

## Security
- VPC with private subnets for data processing
- IAM roles with least privilege access
- S3 bucket encryption and access controls
- Redshift encryption at rest and in transit
"""
        
        with open(docs_dir / 'architecture.md', 'w') as f:
            f.write(diagram_content)
    
    def create_runbooks(self):
        """Create operational runbooks"""
        docs_dir = self.project_root / 'docs'
        
        runbooks = {
            'adding_new_data_sources.md': """
# Adding New Data Sources

## Steps
1. Update data pipeline scripts in `pipelines/`
2. Add new staging models in `dbt/models/staging/`
3. Update core models and marts
4. Add data quality tests
5. Update Airflow DAGs
6. Test with sample data
7. Deploy to production

## Example
```sql
-- Add new staging model
{{ config(materialized='view') }}
select * from {{ source('raw', 'new_data_source') }}
```
""",
            'updating_quality_checks.md': """
# Updating Data Quality Checks

## Steps
1. Identify data quality issues
2. Update Great Expectations suite
3. Modify validation logic in ETL scripts
4. Update alerting thresholds
5. Test with sample data
6. Deploy changes
7. Monitor results

## Example
```python
# Add new quality check
expectation = df.expect_column_values_to_be_between(
    column="amount",
    min_value=0,
    max_value=1000000
)
```
""",
            'backfilling_data.md': """
# Backfilling Data

## Steps
1. Identify date range for backfill
2. Generate sample data for the period
3. Run batch ETL pipeline
4. Execute dbt models
5. Verify data quality
6. Update analytics tables
7. Monitor performance

## Commands
```bash
# Run backfill
python pipelines/batch_etl.py s3-bucket 2024-01-01

# Run dbt for specific date
dbt run --vars '{"backfill_date": "2024-01-01"}'
```
"""
        }
        
        for filename, content in runbooks.items():
            with open(docs_dir / filename, 'w') as f:
                f.write(content)
    
    def run_complete_setup(self) -> bool:
        """Run complete setup process"""
        logger.info("Starting Regional Development Bank Data Platform Setup")
        logger.info(f"Environment: {self.environment}")
        logger.info(f"Region: {self.region}")
        
        # Check prerequisites
        if not self.check_prerequisites():
            return False
        
        # Setup AWS credentials
        if not self.setup_aws_credentials():
            return False
        
        # Deploy infrastructure
        if not self.deploy_infrastructure():
            return False
        
        # Setup data pipeline
        if not self.setup_data_pipeline():
            return False
        
        # Setup monitoring
        if not self.setup_monitoring():
            return False
        
        # Setup Airflow
        if not self.setup_airflow():
            return False
        
        # Generate sample data
        if not self.generate_sample_data():
            return False
        
        # Setup dbt
        if not self.setup_dbt():
            return False
        
        # Create documentation
        if not self.create_documentation():
            return False
        
        logger.info("🎉 Regional Development Bank Data Platform Setup Completed!")
        logger.info("\nAccess Points:")
        logger.info("- Airflow UI: http://localhost:8080")
        logger.info("- dbt Docs: http://localhost:8080/docs")
        logger.info("- CloudWatch Dashboard: AWS Console")
        logger.info("- S3 Data Lake: AWS Console")
        
        return True


def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Regional Development Bank Data Platform Setup')
    parser.add_argument('--environment', default='dev', choices=['dev', 'staging', 'prod'],
                       help='Environment to deploy (default: dev)')
    parser.add_argument('--region', default='us-east-1',
                       help='AWS region (default: us-east-1)')
    parser.add_argument('--skip-infrastructure', action='store_true',
                       help='Skip infrastructure deployment')
    parser.add_argument('--skip-airflow', action='store_true',
                       help='Skip Airflow setup')
    
    args = parser.parse_args()
    
    # Initialize setup
    setup = DataPlatformSetup(args.environment, args.region)
    
    # Run setup
    success = setup.run_complete_setup()
    
    if success:
        logger.info("Setup completed successfully!")
        sys.exit(0)
    else:
        logger.error("Setup failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()

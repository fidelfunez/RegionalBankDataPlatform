"""
Regional Development Bank Data Pipeline DAG

This DAG orchestrates the complete data pipeline for the Regional Development Bank,
including batch ETL, streaming processing, data quality checks, and analytics.

Author: Data Engineering Team
Date: 2024
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.operators.dummy import DummyOperator
from airflow.providers.amazon.aws.operators.glue import AwsGlueJobOperator
from airflow.providers.amazon.aws.operators.glue_crawler import AwsGlueCrawlerOperator
from airflow.providers.amazon.aws.sensors.glue import AwsGlueJobSensor
from airflow.providers.amazon.aws.sensors.glue_crawler import AwsGlueCrawlerSensor
from airflow.providers.postgres.operators.postgres import PostgresOperator
from airflow.models import Variable
import os

# Default arguments
default_args = {
    'owner': 'data-engineering',
    'depends_on_past': False,
    'start_date': datetime(2024, 1, 1),
    'email_on_failure': True,
    'email_on_retry': False,
    'retries': 3,
    'retry_delay': timedelta(minutes=5),
    'catchup': False,
}

# DAG configuration
dag = DAG(
    'regional_bank_data_pipeline',
    default_args=default_args,
    description='Regional Development Bank Data Pipeline',
    schedule_interval='0 2 * * *',  # Daily at 2 AM
    max_active_runs=1,
    tags=['regional-bank', 'data-pipeline', 'etl'],
)

# Variables
S3_BUCKET = Variable.get("s3_bucket", "dev-regional-bank-data-lake")
KINESIS_STREAM = Variable.get("kinesis_stream", "dev-regional-bank")
REDSHIFT_CLUSTER = Variable.get("redshift_cluster", "dev-regional-bank-redshift")
GLUE_JOB_BATCH = Variable.get("glue_job_batch", "batch-etl-job")
GLUE_JOB_STREAMING = Variable.get("glue_job_streaming", "streaming-etl-job")

# Task functions
def get_processing_date(**context):
    """Get the processing date for the pipeline"""
    execution_date = context['execution_date']
    processing_date = execution_date.strftime('%Y-%m-%d')
    context['task_instance'].xcom_push(key='processing_date', value=processing_date)
    return processing_date

def check_data_quality(**context):
    """Check data quality metrics"""
    processing_date = context['task_instance'].xcom_pull(task_ids='get_processing_date', key='processing_date')
    
    # This would typically call Great Expectations or similar data quality framework
    print(f"Running data quality checks for {processing_date}")
    
    # Simulate data quality checks
    quality_score = 0.95  # This would be calculated from actual data
    
    if quality_score < 0.9:
        raise ValueError(f"Data quality score {quality_score} is below threshold")
    
    return quality_score

def trigger_dbt_run(**context):
    """Trigger dbt run for data modeling"""
    processing_date = context['task_instance'].xcom_pull(task_ids='get_processing_date', key='processing_date')
    
    print(f"Triggering dbt run for {processing_date}")
    
    # This would typically trigger dbt run via API or command line
    return "dbt_run_completed"

def send_notification(**context):
    """Send notification about pipeline completion"""
    processing_date = context['task_instance'].xcom_pull(task_ids='get_processing_date', key='processing_date')
    
    print(f"Sending notification for pipeline completion on {processing_date}")
    
    # This would typically send email/Slack notification
    return "notification_sent"

# Start task
start = DummyOperator(
    task_id='start',
    dag=dag,
)

# Get processing date
get_date = PythonOperator(
    task_id='get_processing_date',
    python_callable=get_processing_date,
    dag=dag,
)

# Batch ETL Job
batch_etl_job = AwsGlueJobOperator(
    task_id='batch_etl_job',
    job_name=GLUE_JOB_BATCH,
    script_location=f's3://{S3_BUCKET}/scripts/batch_etl.py',
    s3_bucket=S3_BUCKET,
    iam_role_name='AWSGlueServiceRole',
    region_name='us-east-1',
    dag=dag,
)

# Batch ETL Job Sensor
batch_etl_sensor = AwsGlueJobSensor(
    task_id='batch_etl_sensor',
    job_name=GLUE_JOB_BATCH,
    run_id=batch_etl_job.output,
    aws_conn_id='aws_default',
    dag=dag,
)

# Data Quality Check
data_quality_check = PythonOperator(
    task_id='data_quality_check',
    python_callable=check_data_quality,
    dag=dag,
)

# Glue Crawler for processed data
glue_crawler = AwsGlueCrawlerOperator(
    task_id='glue_crawler',
    crawler_name='regional-bank-processed-crawler',
    aws_conn_id='aws_default',
    dag=dag,
)

# Glue Crawler Sensor
crawler_sensor = AwsGlueCrawlerSensor(
    task_id='crawler_sensor',
    crawler_name='regional-bank-processed-crawler',
    aws_conn_id='aws_default',
    dag=dag,
)

# dbt Run
dbt_run = PythonOperator(
    task_id='dbt_run',
    python_callable=trigger_dbt_run,
    dag=dag,
)

# dbt Test
dbt_test = BashOperator(
    task_id='dbt_test',
    bash_command='cd /opt/airflow/dbt && dbt test',
    dag=dag,
)

# dbt Docs Generate
dbt_docs = BashOperator(
    task_id='dbt_docs',
    bash_command='cd /opt/airflow/dbt && dbt docs generate',
    dag=dag,
)

# Update Redshift tables
update_redshift = PostgresOperator(
    task_id='update_redshift',
    postgres_conn_id='redshift_default',
    sql="""
    -- Refresh materialized views
    REFRESH MATERIALIZED VIEW marts.regional_analytics;
    
    -- Update statistics
    ANALYZE;
    """,
    dag=dag,
)

# Streaming ETL Job (continuous)
streaming_etl_job = AwsGlueJobOperator(
    task_id='streaming_etl_job',
    job_name=GLUE_JOB_STREAMING,
    script_location=f's3://{S3_BUCKET}/scripts/streaming_etl.py',
    s3_bucket=S3_BUCKET,
    iam_role_name='AWSGlueServiceRole',
    region_name='us-east-1',
    dag=dag,
)

# Send notification
notification = PythonOperator(
    task_id='send_notification',
    python_callable=send_notification,
    dag=dag,
)

# End task
end = DummyOperator(
    task_id='end',
    dag=dag,
)

# Task dependencies
start >> get_date

# Batch processing pipeline
get_date >> batch_etl_job >> batch_etl_sensor >> data_quality_check

# Data catalog and modeling
data_quality_check >> glue_crawler >> crawler_sensor >> dbt_run

# dbt pipeline
dbt_run >> dbt_test >> dbt_docs >> update_redshift

# Streaming pipeline (runs independently)
get_date >> streaming_etl_job

# Final steps
update_redshift >> notification >> end

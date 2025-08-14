#!/usr/bin/env python3
"""
CloudWatch Monitoring and Alerting Setup for Regional Bank Data Platform

This script sets up CloudWatch alarms and monitoring for:
- Pipeline failures
- Data quality issues
- Performance metrics
- Cost optimization

Author: Data Engineering Team
Date: 2024
"""

import boto3
import json
import logging
from typing import Dict, List, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class CloudWatchMonitor:
    """CloudWatch monitoring and alerting setup"""
    
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self.cloudwatch = boto3.client('cloudwatch', region_name=region)
        self.sns = boto3.client('sns', region_name=region)
        
    def create_sns_topic(self, topic_name: str) -> str:
        """Create SNS topic for notifications"""
        try:
            response = self.sns.create_topic(Name=topic_name)
            topic_arn = response['TopicArn']
            logger.info(f"Created SNS topic: {topic_arn}")
            return topic_arn
        except Exception as e:
            logger.error(f"Error creating SNS topic: {e}")
            raise
    
    def create_pipeline_failure_alarm(self, 
                                    alarm_name: str,
                                    topic_arn: str,
                                    glue_job_name: str) -> str:
        """Create alarm for Glue job failures"""
        
        alarm_config = {
            'AlarmName': alarm_name,
            'AlarmDescription': f'Alert when {glue_job_name} fails',
            'MetricName': 'FailedTaskCount',
            'Namespace': 'AWS/Glue',
            'Statistic': 'Sum',
            'Period': 300,  # 5 minutes
            'EvaluationPeriods': 2,
            'Threshold': 1,
            'ComparisonOperator': 'GreaterThanOrEqualToThreshold',
            'TreatMissingData': 'notBreaching',
            'Dimensions': [
                {
                    'Name': 'JobName',
                    'Value': glue_job_name
                }
            ],
            'AlarmActions': [topic_arn],
            'OKActions': [topic_arn]
        }
        
        try:
            response = self.cloudwatch.put_metric_alarm(**alarm_config)
            logger.info(f"Created pipeline failure alarm: {alarm_name}")
            return response['ResponseMetadata']['RequestId']
        except Exception as e:
            logger.error(f"Error creating pipeline failure alarm: {e}")
            raise
    
    def create_data_quality_alarm(self,
                                alarm_name: str,
                                topic_arn: str,
                                metric_name: str = 'DataQualityScore') -> str:
        """Create alarm for data quality issues"""
        
        alarm_config = {
            'AlarmName': alarm_name,
            'AlarmDescription': 'Alert when data quality score is below threshold',
            'MetricName': metric_name,
            'Namespace': 'Custom/DataQuality',
            'Statistic': 'Average',
            'Period': 300,  # 5 minutes
            'EvaluationPeriods': 1,
            'Threshold': 0.9,  # 90% quality threshold
            'ComparisonOperator': 'LessThanThreshold',
            'TreatMissingData': 'breaching',
            'AlarmActions': [topic_arn],
            'OKActions': [topic_arn]
        }
        
        try:
            response = self.cloudwatch.put_metric_alarm(**alarm_config)
            logger.info(f"Created data quality alarm: {alarm_name}")
            return response['ResponseMetadata']['RequestId']
        except Exception as e:
            logger.error(f"Error creating data quality alarm: {e}")
            raise
    
    def create_performance_alarm(self,
                               alarm_name: str,
                               topic_arn: str,
                               service: str,
                               metric: str,
                               threshold: float) -> str:
        """Create performance monitoring alarm"""
        
        alarm_config = {
            'AlarmName': alarm_name,
            'AlarmDescription': f'Performance alert for {service} {metric}',
            'MetricName': metric,
            'Namespace': f'AWS/{service}',
            'Statistic': 'Average',
            'Period': 300,  # 5 minutes
            'EvaluationPeriods': 2,
            'Threshold': threshold,
            'ComparisonOperator': 'GreaterThanThreshold',
            'TreatMissingData': 'notBreaching',
            'AlarmActions': [topic_arn],
            'OKActions': [topic_arn]
        }
        
        try:
            response = self.cloudwatch.put_metric_alarm(**alarm_config)
            logger.info(f"Created performance alarm: {alarm_name}")
            return response['ResponseMetadata']['RequestId']
        except Exception as e:
            logger.error(f"Error creating performance alarm: {e}")
            raise
    
    def create_cost_alarm(self,
                         alarm_name: str,
                         topic_arn: str,
                         service: str,
                         threshold: float) -> str:
        """Create cost monitoring alarm"""
        
        alarm_config = {
            'AlarmName': alarm_name,
            'AlarmDescription': f'Cost alert for {service}',
            'MetricName': 'EstimatedCharges',
            'Namespace': 'AWS/Billing',
            'Statistic': 'Maximum',
            'Period': 86400,  # 24 hours
            'EvaluationPeriods': 1,
            'Threshold': threshold,
            'ComparisonOperator': 'GreaterThanThreshold',
            'TreatMissingData': 'notBreaching',
            'Dimensions': [
                {
                    'Name': 'ServiceName',
                    'Value': service
                },
                {
                    'Name': 'Currency',
                    'Value': 'USD'
                }
            ],
            'AlarmActions': [topic_arn],
            'OKActions': [topic_arn]
        }
        
        try:
            response = self.cloudwatch.put_metric_alarm(**alarm_config)
            logger.info(f"Created cost alarm: {alarm_name}")
            return response['ResponseMetadata']['RequestId']
        except Exception as e:
            logger.error(f"Error creating cost alarm: {e}")
            raise
    
    def create_custom_metric(self,
                           namespace: str,
                           metric_name: str,
                           value: float,
                           unit: str = 'Count',
                           dimensions: Optional[List[Dict]] = None) -> str:
        """Create custom metric"""
        
        metric_data = {
            'MetricName': metric_name,
            'Value': value,
            'Unit': unit
        }
        
        if dimensions:
            metric_data['Dimensions'] = dimensions
        
        try:
            response = self.cloudwatch.put_metric_data(
                Namespace=namespace,
                MetricData=[metric_data]
            )
            logger.info(f"Created custom metric: {namespace}/{metric_name}")
            return response['ResponseMetadata']['RequestId']
        except Exception as e:
            logger.error(f"Error creating custom metric: {e}")
            raise
    
    def setup_complete_monitoring(self, environment: str) -> Dict[str, str]:
        """Setup complete monitoring for the data platform"""
        
        logger.info(f"Setting up monitoring for environment: {environment}")
        
        # Create SNS topic
        topic_name = f"{environment}-regional-bank-alerts"
        topic_arn = self.create_sns_topic(topic_name)
        
        # Create alarms
        alarms = {}
        
        # Pipeline failure alarms
        alarms['batch_etl_failure'] = self.create_pipeline_failure_alarm(
            f"{environment}-batch-etl-failure",
            topic_arn,
            f"{environment}-batch-etl-job"
        )
        
        alarms['streaming_etl_failure'] = self.create_pipeline_failure_alarm(
            f"{environment}-streaming-etl-failure",
            topic_arn,
            f"{environment}-streaming-etl-job"
        )
        
        # Data quality alarms
        alarms['data_quality'] = self.create_data_quality_alarm(
            f"{environment}-data-quality-alert",
            topic_arn
        )
        
        # Performance alarms
        alarms['redshift_performance'] = self.create_performance_alarm(
            f"{environment}-redshift-cpu-high",
            topic_arn,
            'Redshift',
            'CPUUtilization',
            80.0
        )
        
        alarms['s3_errors'] = self.create_performance_alarm(
            f"{environment}-s3-errors",
            topic_arn,
            'S3',
            'NumberOfErrors',
            1.0
        )
        
        # Cost alarms
        alarms['glue_cost'] = self.create_cost_alarm(
            f"{environment}-glue-cost-alert",
            topic_arn,
            'AWSGlue',
            100.0  # $100 threshold
        )
        
        alarms['redshift_cost'] = self.create_cost_alarm(
            f"{environment}-redshift-cost-alert",
            topic_arn,
            'AmazonRedshift',
            200.0  # $200 threshold
        )
        
        logger.info(f"Created {len(alarms)} alarms for {environment}")
        return alarms
    
    def create_dashboard(self, dashboard_name: str, environment: str) -> str:
        """Create CloudWatch dashboard"""
        
        dashboard_body = {
            "widgets": [
                {
                    "type": "metric",
                    "x": 0,
                    "y": 0,
                    "width": 12,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            ["AWS/Glue", "FailedTaskCount", "JobName", f"{environment}-batch-etl-job"],
                            [".", "SucceededTaskCount", ".", "."]
                        ],
                        "view": "timeSeries",
                        "stacked": False,
                        "region": self.region,
                        "title": "Glue Job Status",
                        "period": 300
                    }
                },
                {
                    "type": "metric",
                    "x": 12,
                    "y": 0,
                    "width": 12,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            ["AWS/Redshift", "CPUUtilization"],
                            ["AWS/Redshift", "DatabaseConnections"]
                        ],
                        "view": "timeSeries",
                        "stacked": False,
                        "region": self.region,
                        "title": "Redshift Performance",
                        "period": 300
                    }
                },
                {
                    "type": "metric",
                    "x": 0,
                    "y": 6,
                    "width": 12,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            ["Custom/DataQuality", "DataQualityScore"]
                        ],
                        "view": "timeSeries",
                        "stacked": False,
                        "region": self.region,
                        "title": "Data Quality Score",
                        "period": 300
                    }
                },
                {
                    "type": "metric",
                    "x": 12,
                    "y": 6,
                    "width": 12,
                    "height": 6,
                    "properties": {
                        "metrics": [
                            ["AWS/Billing", "EstimatedCharges", "ServiceName", "AWSGlue"],
                            [".", ".", ".", "AmazonRedshift"],
                            [".", ".", ".", "AmazonS3"]
                        ],
                        "view": "timeSeries",
                        "stacked": False,
                        "region": self.region,
                        "title": "Cost Monitoring",
                        "period": 86400
                    }
                }
            ]
        }
        
        try:
            response = self.cloudwatch.put_dashboard(
                DashboardName=dashboard_name,
                DashboardBody=json.dumps(dashboard_body)
            )
            logger.info(f"Created dashboard: {dashboard_name}")
            return response['ResponseMetadata']['RequestId']
        except Exception as e:
            logger.error(f"Error creating dashboard: {e}")
            raise


def main():
    """Main function to setup monitoring"""
    
    # Initialize monitor
    monitor = CloudWatchMonitor()
    
    # Setup monitoring for different environments
    environments = ['dev', 'staging', 'prod']
    
    for env in environments:
        try:
            # Setup complete monitoring
            alarms = monitor.setup_complete_monitoring(env)
            
            # Create dashboard
            dashboard_name = f"{env}-regional-bank-dashboard"
            monitor.create_dashboard(dashboard_name, env)
            
            print(f"Successfully setup monitoring for {env}")
            print(f"Created {len(alarms)} alarms")
            
        except Exception as e:
            print(f"Error setting up monitoring for {env}: {e}")


if __name__ == "__main__":
    main()

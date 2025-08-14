#!/usr/bin/env python3
"""
Screenshot Guide for Regional Bank Data Platform Portfolio
This script provides guidance on what screenshots to take for your portfolio.
"""

import os
import sys
from datetime import datetime

def print_screenshot_guide():
    """Print a comprehensive guide for taking portfolio screenshots."""
    
    print("=" * 80)
    print("📸 SCREENSHOT GUIDE FOR DATA ENGINEERING PORTFOLIO")
    print("=" * 80)
    print()
    
    print("🎯 IMPORTANT: Take these screenshots AFTER deploying your infrastructure!")
    print()
    
    screenshots = {
        "Infrastructure Deployment": [
            "1. Terraform deployment success (terminal showing 'Apply complete!')",
            "2. AWS Console - S3 bucket created with data lake structure",
            "3. AWS Console - Redshift cluster running",
            "4. AWS Console - Glue jobs created",
            "5. AWS Console - Kinesis streams active"
        ],
        
        "Data Pipeline Execution": [
            "1. Airflow UI (localhost:8080) - DAGs running successfully",
            "2. Airflow UI - DAG graph view showing all tasks completed",
            "3. Glue Console - Job execution logs showing success",
            "4. S3 Console - Data files in processed/curated folders",
            "5. Terminal - Sample data generation script output"
        ],
        
        "Data Quality & Validation": [
            "1. dbt test results (terminal showing all tests passed)",
            "2. dbt docs lineage graph (localhost:8080/docs)",
            "3. Great Expectations validation report (if implemented)",
            "4. Data quality metrics in CloudWatch"
        ],
        
        "Data Warehouse & Analytics": [
            "1. Redshift query editor - Sample query results",
            "2. dbt docs - Model documentation and lineage",
            "3. Analytics dashboard (if created)",
            "4. Sample data in final marts tables"
        ],
        
        "Monitoring & Alerting": [
            "1. CloudWatch dashboard showing pipeline metrics",
            "2. CloudWatch alarms configuration",
            "3. SNS notification email (if alerts triggered)",
            "4. Pipeline health metrics and performance"
        ]
    }
    
    for category, shots in screenshots.items():
        print(f"📋 {category.upper()}")
        print("-" * 50)
        for shot in shots:
            print(f"   {shot}")
        print()
    
    print("=" * 80)
    print("💡 TIPS FOR GREAT SCREENSHOTS:")
    print("=" * 80)
    print()
    print("1. 📱 Use high resolution (1920x1080 or higher)")
    print("2. 🎨 Focus on the important parts of each screen")
    print("3. 📝 Add annotations if needed to highlight key points")
    print("4. 🗂️  Organize screenshots by category")
    print("5. 📅 Take screenshots during actual pipeline execution")
    print("6. 🔍 Make sure error messages are resolved before taking shots")
    print()
    
    print("🚀 READY TO DEPLOY?")
    print("Run: python scripts/setup_pipeline.py --environment dev")
    print()
    
    print("📸 AFTER DEPLOYMENT:")
    print("1. Follow the screenshot guide above")
    print("2. Replace [Screenshot: ...] placeholders in README.md")
    print("3. Add your contact information to the README")
    print("4. Create a GitHub repository and push your code")
    print("5. Share the repository link with hiring managers!")
    print()

def create_screenshot_checklist():
    """Create a checklist file for screenshots."""
    
    checklist_content = """# Screenshot Checklist for Portfolio

## Infrastructure Deployment
- [ ] Terraform deployment success
- [ ] AWS S3 bucket with data lake structure
- [ ] AWS Redshift cluster running
- [ ] AWS Glue jobs created
- [ ] AWS Kinesis streams active

## Data Pipeline Execution
- [ ] Airflow UI - DAGs running successfully
- [ ] Airflow UI - DAG graph view
- [ ] Glue job execution logs
- [ ] S3 processed/curated data
- [ ] Sample data generation output

## Data Quality & Validation
- [ ] dbt test results passing
- [ ] dbt docs lineage graph
- [ ] Great Expectations validation
- [ ] Data quality metrics

## Data Warehouse & Analytics
- [ ] Redshift query results
- [ ] dbt model documentation
- [ ] Analytics dashboard
- [ ] Final marts data

## Monitoring & Alerting
- [ ] CloudWatch dashboard
- [ ] CloudWatch alarms
- [ ] SNS notifications
- [ ] Pipeline health metrics

## Portfolio Preparation
- [ ] Update README with screenshots
- [ ] Add contact information
- [ ] Create GitHub repository
- [ ] Test all links work
- [ ] Review for typos/errors
"""
    
    with open("SCREENSHOT_CHECKLIST.md", "w") as f:
        f.write(checklist_content)
    
    print("✅ Created SCREENSHOT_CHECKLIST.md")
    print("📋 Use this checklist to track your screenshot progress!")

if __name__ == "__main__":
    print_screenshot_guide()
    create_screenshot_checklist()

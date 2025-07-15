#!/bin/bash
# Basic automation: install dependencies and setup cron

echo "Installing Python dependencies..."
pip3 install -r requirements.txt

echo "Setting up cron job for log fetching..."
CRON="*/5 * * * * cd ~/real_time_monitoring/data_collection && /usr/bin/python3 fetch_cloudwatch_logs.py"
( crontab -l | grep -v 'fetch_cloudwatch_logs.py' ; echo "$CRON" ) | crontab -

echo "All set! You can now run your dashboard:"
echo "cd ~/real_time_monitoring/data_collection && streamlit run dashboard.py"

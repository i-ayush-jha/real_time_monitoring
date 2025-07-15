Real-Time AWS CloudWatch Log Monitoring & Alerting System
Overview
This project is a production-ready system for:
Fetching logs from AWS CloudWatch (for example, Flask app logs from EC2),
Parsing and storing logs locally,
Real-time visualization in an interactive Streamlit dashboard,
Automatic anomaly detection (including Machine Learning with Isolation Forest),
Download and email features for logs,
Automation via cron jobs,
(Optional) HTTPS and authentication for security.

It’s designed for DevOps teams, engineers, or students who want to:
Monitor application errors, warnings, and activity,
Be alerted instantly via email/SMS,
Investigate log trends and anomalies,
Share dashboards or automate monitoring tasks.


        +-------------------+         +--------------------+
        |   AWS CloudWatch  |<------->|   EC2 (Flask App)  |
        +-------------------+         +--------------------+
                  |                            ^
                  v                            |
      +----------------------------+           |
      | fetch_cloudwatch_logs.py   |-----------+
      +----------------------------+
                  |
          (Local output_logs.txt)
                  |
         +------------------------+
         |   Streamlit Dashboard  |
         |   (dashboard.py)       |
         +------------------------+
                |         |
         [Email/SMS]   [Download/Share]


Block Descriptions:
AWS CloudWatch: Stores logs from your Flask app running on EC2.Features
Automated log fetching from AWS CloudWatch
Real-time dashboard (Streamlit)
Filtering by date, log type, search
Auto-refresh and logs pagination
Log level distribution charts
Statistical and ML-based anomaly detection (Isolation Forest)
Download logs (.txt/.xlsx)
Send filtered logs via email from dashboard
(Optional) Secure with HTTPS and authentication
Fully automated (via cron job/setup script)

Easy sharing: zip file, Google Drive, or GitHub
fetch_cloudwatch_logs.py: Python script to fetch, parse, and save logs locally.
output_logs.txt: The local file holding parsed logs for dashboard use.
dashboard.py (Streamlit): Interactive, real-time dashboard for viewing, filtering, and analyzing logs. Supports anomaly detection and email/download features.

Prerequisites
AWS Account (with CloudWatch logs and an EC2 instance running your app)
IAM role/user with access to CloudWatch Logs and (optionally) SES for email
Python 3.7+
(For full features) AWS SES verified email


Quick Start Guide
1. Clone or Download the Repository
git clone https://github.com/YOUR_USERNAME/real_time_monitoring.git
cd real_time_monitoring/data_collection
Or download the zip, extract, and cd to data_collection.


2. Install Python Dependencies
pip install -r requirements.txt

4. Configure AWS Credentials
If running on EC2 with IAM Role: No extra steps needed.
If running locally, run:
aws configure
Or set your credentials via environment variables.

4. Set Up Log Fetching
Edit your log group and region in fetch_cloudwatch_logs.py if needed.

To fetch logs once:
python3 fetch_cloudwatch_logs.py

5. Automate with Cron (on Linux/EC2)
Open cron editor:
crontab -e
Add this line at the end (replace path and python if needed):
*/5 * * * * cd /home/ec2-user/real_time_monitoring/data_collection && /usr/bin/python3 fetch_cloudwatch_logs.py
This runs the fetch script every 5 minutes.

6. Run the Dashboard
From data_collection:
streamlit run dashboard.py
Dashboard will open at http://<your-ec2-ip>:8501

(Optional) Use key.pem and HTTPS for secure access.

Using the Dashboard
Filters: Choose date range, log type, or search text.
Show All Logs: Checkbox to ignore date range and display everything.
Charts: Visualize error/warning/other counts, spot spikes, see anomalies.
Download: Export filtered logs as .txt or .xlsx (Excel).
Email: Send filtered logs via SES (set SES_EMAIL in dashboard.py).
Anomaly Detection: Switch between hourly/minutely, see and download intervals flagged as outliers.
Pagination: View logs in chunks (e.g., 20, 50, 100 per page).

8. Security (Production)
Restrict EC2 security group: Only open necessary ports (22/5000/8501) to your IP.
Set up HTTPS: Use NGINX with Let's Encrypt or Streamlit's SSL options.
Enable authentication: Protect dashboard with NGINX auth_basic or similar.

9. Sharing the Project
Google Drive/OneDrive: Zip the folder and share.
GitHub: git add ., git commit -m "init", git remote add origin ..., git push.
Email: Download zip, attach, and send to teammates.

FAQ / Troubleshooting
Dashboard says “no logs found”

Check if output_logs.txt exists and has data.
Run python3 fetch_cloudwatch_logs.py to create/fill the file.
Email not sending
Make sure SES_EMAIL is verified in AWS SES.
Check AWS SES region and credentials.

Graphs not updating
Ensure cron job is running (crontab -l), or run the fetch script manually.

Permission errors
Try chmod +x setup.sh or run with sudo if needed.

Log fetch errors
Check IAM permissions, region, and log group names.

Project Structure
real_time_monitoring/
│
├── data_collection/
│   ├── dashboard.py            # Streamlit dashboard
│   ├── fetch_cloudwatch_logs.py# AWS log fetcher
│   ├── output_logs.txt         # Local log file (auto-generated)
│   ├── cert.pem, key.pem       # (Optional) SSL keys for HTTPS
│   ├── requirements.txt        # Python dependencies
│   └── ...
├── app.py                      # Example Flask app (optional)
├── setup.sh                    # Automation script (optional)
├── README.md                   # This file!
└── ...

import boto3
import time
import os

# CONFIGURATION
REGION = "ap-south-1"                  # Your AWS region
LOG_GROUP = "/aws/ec2/flask-app"       # Your CloudWatch log group
YOUR_EMAIL = "ayushexpertise@gmail.com"  # Must be SES-verified
LAST_ALERT_FILE = "last_alert.txt"     # File to track last alerted error

client = boto3.client('logs', region_name=REGION)

def get_log_stream():
    """Get the latest log stream name."""
    streams = client.describe_log_streams(
        logGroupName=LOG_GROUP,
        orderBy='LastEventTime',
        descending=True,
        limit=1
    )
    return streams['logStreams'][0]['logStreamName']

def fetch_latest_error():
    """Return the most recent error log message (or None if no new error)."""
    log_stream = get_log_stream()
    now = int(time.time() * 1000)
    past = now - (60 * 60 * 1000)  # last 1 hour
    response = client.get_log_events(
        logGroupName=LOG_GROUP,
        logStreamName=log_stream,
        startTime=past,
        endTime=now,
        startFromHead=True
    )
    # Find the latest error log
    errors = [e['message'] for e in response['events'] if "error" in e['message'].lower()]
    if errors:
        return errors[-1]   # Most recent error
    return None

def has_alerted(error_message):
    """Check if this error has already been alerted."""
    if not os.path.exists(LAST_ALERT_FILE):
        return False
    with open(LAST_ALERT_FILE, "r") as f:
        last = f.read().strip()
        return last == error_message

def update_last_alert(error_message):
    """Update the last alerted error."""
    with open(LAST_ALERT_FILE, "w") as f:
        f.write(error_message)

def send_email(error_message):
    """Send error email via AWS SES."""
    ses = boto3.client('ses', region_name=REGION)
    ses.send_email(
        Source=YOUR_EMAIL,
        Destination={'ToAddresses': [YOUR_EMAIL]},
        Message={
            'Subject': {'Data': '🚨 CloudWatch Error Alert'},
            'Body': {
                'Html': {
                    'Data': f"""
                    <h2>CloudWatch Error Detected</h2>
                    <pre>{error_message}</pre>
                    <p><b>Time:</b> {time.strftime('%Y-%m-%d %H:%M:%S')}</p>
                    """
                }
            }
        }
    )
    print("Error alert sent!")

if __name__ == "__main__":
    error = fetch_latest_error()
    if error:
        if not has_alerted(error):
            print("[ALERT] New error found, sending email...")
            send_email(error)
            update_last_alert(error)
        else:
            print("[INFO] Error already alerted, not sending duplicate.")
    else:
        print("[INFO] No error found in the last hour.")


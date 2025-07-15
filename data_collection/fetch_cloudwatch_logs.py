import boto3
import time

# Set your AWS region and CloudWatch log group name
REGION = "ap-south-1"
LOG_GROUP = "/aws/ec2/flask-app"

client = boto3.client('logs', region_name=REGION)

def get_log_streams():
    streams = client.describe_log_streams(
        logGroupName=LOG_GROUP,
        orderBy='LastEventTime',
        descending=True,
        limit=1
    )
    return streams['logStreams'][0]['logStreamName']

def fetch_logs():
    log_stream = get_log_streams()
    now = int(time.time() * 1000)
    past = now - (60 * 60 * 1000)  # last 1 hour in milliseconds
    response = client.get_log_events(
        logGroupName=LOG_GROUP,
        logStreamName=log_stream,
        startTime=past,
        endTime=now,
        startFromHead=True
    )
    for event in response['events']:
        yield event['message']

if __name__ == "__main__":
    with open("output_logs.txt", "a") as f:
        for log in fetch_logs():
            f.write(log + "\n")















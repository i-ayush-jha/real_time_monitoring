from flask import Flask
import logging
import watchtower

# --- Watchtower Logging Setup ---
logging.basicConfig(level=logging.INFO)
cloudwatch_handler = watchtower.CloudWatchLogHandler(
    log_group='/aws/ec2/flask-app'
)
logging.getLogger('').addHandler(cloudwatch_handler)
# --- End Watchtower Setup ---

app = Flask(__name__)

@app.route('/')
def home():
    logging.info("Home endpoint was hit!")
    return "Hello, CloudWatch!"

@app.route('/error')
def error():
    logging.error("This is a test error log!")
    return "Error route hit!", 500

if __name__ == '__main__':
    app.run(host='0.0.0.0')

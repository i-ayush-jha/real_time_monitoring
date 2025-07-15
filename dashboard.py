import streamlit as st
import pandas as pd
from sklearn.ensemble import IsolationForest
from datetime import datetime

# --- Load and parse log file ---
log_file = "output_logs.txt"

with open(log_file) as f:
    logs = f.readlines()

# Basic log parsing (customize as per your log format!)
parsed_logs = []
for line in logs:
    # Try to extract timestamp and error
    try:
        ts = line.split('[')[1].split(']')[0]
        dt = datetime.strptime(ts, "%d/%b/%Y %H:%M:%S")
        error_flag = "error" in line.lower() or "500" in line
        parsed_logs.append({'raw': line, 'timestamp': dt, 'is_error': error_flag})
    except Exception:
        parsed_logs.append({'raw': line, 'timestamp': None, 'is_error': False})

df = pd.DataFrame(parsed_logs)
df = df.dropna(subset=['timestamp'])

# --- ML: Anomaly Detection ---
anomaly_detected = []
if len(df) > 0:
    # For demo: Use error log times (could be improved by adding more features)
    times = df['timestamp'].map(datetime.timestamp).values.reshape(-1, 1)
    if len(times) > 10:  # IsolationForest needs several points
        model = IsolationForest(contamination=0.05)
        df['anomaly'] = model.fit_predict(times)
    else:
        df['anomaly'] = 1
else:
    df['anomaly'] = []

# --- Streamlit Dashboard UI ---
st.title("CloudWatch Log Dashboard + ML Anomaly Detection")
st.write("Total logs:", len(df))
st.write("Error logs:", df['is_error'].sum())
st.write("Anomalies detected:", (df['anomaly'] == -1).sum())

st.dataframe(df[['timestamp', 'is_error', 'anomaly', 'raw']])

# Chart: Error vs non-error
st.bar_chart(df['is_error'].value_counts())

# Chart: Anomaly vs normal
if 'anomaly' in df.columns:
    st.bar_chart(df['anomaly'].value_counts())

# Show just anomalies
st.subheader("Anomalous Log Entries")
st.dataframe(df[df['anomaly'] == -1][['timestamp', 'raw']])

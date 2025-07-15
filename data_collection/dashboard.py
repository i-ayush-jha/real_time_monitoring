import streamlit as st
import pandas as pd
import numpy as np
import datetime
import pytz
import matplotlib.pyplot as plt
import re
import io
from sklearn.ensemble import IsolationForest

# ---- SETTINGS ----
LOG_FILE = "output_logs.txt"
IST = pytz.timezone("Asia/Kolkata")
SES_EMAIL = "ayushexpertise@gmail.com"  # <-- Replace with your SES verified email

st.set_page_config(page_title="CloudWatch Log Dashboard", layout="wide")

# ---- Helper Functions ----

def parse_log_line(line):
    dt = None
    match = re.search(r"\[(.*?)\]", line)
    if match:
        try:
            dt = datetime.datetime.strptime(match.group(1), "%d/%b/%Y %H:%M:%S")
            dt = IST.localize(dt)
        except:
            pass
    lline = line.lower()
    if "error" in lline or "500" in lline:
        level = "Error"
    elif "warning" in lline or "warn" in lline:
        level = "Warning"
    else:
        level = "Other"
    return dt, level, line.strip()

@st.cache_data(show_spinner=False)
def load_logs():
    rows = []
    with open(LOG_FILE, encoding="utf-8") as f:
        for line in f:
            dt, level, txt = parse_log_line(line)
            if dt:
                rows.append({"datetime": dt, "level": level, "text": txt})
    df = pd.DataFrame(rows)
    return df.sort_values("datetime", ascending=False).reset_index(drop=True)

def logs_to_text(df):
    return "\n".join(df["text"].tolist())

def logs_to_excel(df):
    df_excel = df.copy()
    if "datetime" in df_excel.columns:
        df_excel["datetime"] = df_excel["datetime"].dt.tz_localize(None)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df_excel.to_excel(writer, index=False, sheet_name="Logs")
    return output.getvalue()

def send_email_via_ses(subject, body, to_email, attachment_bytes=None, attachment_filename=None):
    import boto3
    import email
    from email.mime.multipart import MIMEMultipart
    from email.mime.text import MIMEText
    from email.mime.base import MIMEBase
    from email import encoders

    ses = boto3.client("ses", region_name="ap-south-1")
    msg = MIMEMultipart()
    msg['From'] = to_email
    msg['To'] = to_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    if attachment_bytes and attachment_filename:
        part = MIMEBase('application', "octet-stream")
        part.set_payload(attachment_bytes)
        encoders.encode_base64(part)
        part.add_header('Content-Disposition', f'attachment; filename="{attachment_filename}"')
        msg.attach(part)

    response = ses.send_raw_email(
        Source=to_email,
        Destinations=[to_email],
        RawMessage={'Data': msg.as_string()}
    )
    return response

def aggregate_for_ml(df, resample_rule):
    if df.empty:
        return pd.DataFrame(columns=['date_interval', 'error_count', 'warning_count', 'total_count'])
    agg = df.copy()
    agg['date_interval'] = agg['datetime'].dt.floor(resample_rule)
    error_counts = agg[agg['level'] == 'Error'].groupby('date_interval').size().rename('error_count')
    warn_counts = agg[agg['level'] == 'Warning'].groupby('date_interval').size().rename('warning_count')
    total_counts = agg.groupby('date_interval').size().rename('total_count')
    result = pd.concat([error_counts, warn_counts, total_counts], axis=1).fillna(0)
    return result.reset_index()

# ---- UI ----
st.title("🚀 CloudWatch Log Dashboard")
st.caption("All times shown are in Asia/Kolkata (IST)")

# ---- Sidebar: Filters & Settings ----
with st.sidebar:
    refresh_secs = st.number_input("Auto-refresh interval (sec)", min_value=5, max_value=120, value=30, step=1)
    st.markdown("### Date Range Filter")

# ---- Load Logs ----
df = load_logs()

# ---- Date Filter ----
if not df.empty:
    min_date = df["datetime"].min().date()
    max_date = df["datetime"].max().date()
    date_range = st.sidebar.date_input("Select date range", [min_date, max_date], min_value=min_date, max_value=max_date)
    if isinstance(date_range, (tuple, list)):
        start_date, end_date = date_range
    else:
        start_date = end_date = date_range
    df = df[(df["datetime"].dt.date >= start_date) & (df["datetime"].dt.date <= end_date)]
else:
    st.warning("No log entries found!")
    st.stop()

# ---- Log Type Filter ----
st.sidebar.markdown("### Log Level Filter")
log_types = st.sidebar.multiselect(
    "Select log types to show",
    ["Error", "Warning", "Other"],
    default=["Error", "Warning", "Other"]
)
df = df[df["level"].isin(log_types)] if log_types else df

# ---- Search Filter ----
search = st.text_input("Search logs (supports substring/regex):", value="")
if search:
    try:
        df = df[df["text"].str.contains(search, case=False, na=False, regex=True)]
    except:
        df = df[df["text"].str.contains(search, case=False, na=False)]

now_ist = datetime.datetime.now(IST)
st.write(f"**Last updated:** {now_ist.strftime('%Y-%m-%d %H:%M:%S')} (IST)")

# ---- Log Level Distribution & Z-score Anomaly Detection (Side by Side) ----
col1, col2 = st.columns(2)
with col1:
    st.subheader("Log Level Distribution")
    if not df.empty:
        level_counts = df["level"].value_counts().reindex(["Error", "Warning", "Other"], fill_value=0)
        fig, ax = plt.subplots(figsize=(4,2.2))
        bars = ax.bar(level_counts.index, level_counts.values, color=["#e45756", "#ffc107", "#3498db"])
        for bar, count in zip(bars, level_counts.values):
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height(), str(count), ha='center', va='bottom')
        ax.set_ylabel("Count")
        ax.set_xlabel("Log Level")
        st.pyplot(fig, use_container_width=True)
    else:
        st.info("No logs to show for selected filters.")

with col2:
    st.subheader("Anomaly Detection (Z-score, per hour)")
    if not df.empty:
        perhour = df.groupby(df["datetime"].dt.hour).size()
        mean, std = perhour.mean(), perhour.std()
        z_scores = (perhour - mean) / (std if std > 0 else 1)
        anomalies = perhour[z_scores > 2]
        fig2, ax2 = plt.subplots(figsize=(4,2.2))
        colormap = ["#e45756" if h in anomalies.index else "#4caf50" for h in perhour.index]
        perhour.plot(kind="bar", ax=ax2, color=colormap)
        ax2.set_ylabel("Log Count")
        ax2.set_xlabel("Hour (IST)")
        st.pyplot(fig2, use_container_width=True)
        if not anomalies.empty:
            st.warning(f"🚨 Anomaly: Unusual spike at hours: {', '.join(str(h) for h in anomalies.index)}")
    else:
        st.info("No anomaly data (empty logs after filtering).")

# ---- Download Filtered Logs ----
st.download_button(
    label="⬇️ Download filtered logs (.txt)",
    data=logs_to_text(df),
    file_name="filtered_logs.txt"
)

st.download_button(
    label="⬇️ Download filtered logs (Excel)",
    data=logs_to_excel(df),
    file_name="filtered_logs.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
)

# ---- Email filtered logs as .txt or Excel ----
with st.expander("📧 Send Filtered Logs via Email", expanded=False):
    email_note = st.text_area("Add a note for the email (optional):", key="mail_filtered_logs")
    attach_format = st.selectbox("Attachment format", ["Text (.txt)", "Excel (.xlsx)"])
    if st.button("Send Filtered Logs by Email"):
        try:
            if attach_format == "Text (.txt)":
                att_bytes = logs_to_text(df).encode("utf-8")
                att_fname = "filtered_logs.txt"
            else:
                att_bytes = logs_to_excel(df)
                att_fname = "filtered_logs.xlsx"
            send_email_via_ses(
                subject="🚨 CloudWatch Filtered Logs",
                body=f"Filtered logs sent from dashboard.\n\n{email_note}",
                to_email=SES_EMAIL,
                attachment_bytes=att_bytes,
                attachment_filename=att_fname
            )
            st.success(f"Filtered logs ({att_fname}) sent to {SES_EMAIL}")
        except Exception as e:
            st.error(f"Failed to send email: {e}")

# ---- ML-based Anomaly Detection (Isolation Forest, user selectable scale) ----
st.markdown("---")
st.subheader("ML-based Anomaly Detection (Isolation Forest)")

st.sidebar.markdown("### ML Anomaly Detection Settings")
time_scale = st.sidebar.selectbox(
    "Aggregate log data by:",
    ["Hourly", "Minutely"],
    index=0
)
resample_rule = 'H' if time_scale == "Hourly" else 'T'
agg_df = aggregate_for_ml(df, resample_rule)

if not agg_df.empty and agg_df.shape[0] > 4:
    features = agg_df[['error_count', 'warning_count', 'total_count']]
    model = IsolationForest(contamination=0.07, random_state=42)
    model.fit(features)
    agg_df['anomaly'] = model.predict(features)  # -1 is anomaly, 1 is normal

    fig3, ax3 = plt.subplots(figsize=(8, 2.5))
    ax3.plot(agg_df['date_interval'], agg_df['total_count'], label='Total logs/' + time_scale.lower(), color='#2980b9', marker='o')
    ax3.scatter(agg_df['date_interval'][agg_df['anomaly']==-1], 
                agg_df['total_count'][agg_df['anomaly']==-1], 
                color='red', label='Anomaly', zorder=5, s=80, marker='*')
    ax3.set_xlabel(f"{time_scale}")
    ax3.set_ylabel("Log Count")
    ax3.legend()
    st.pyplot(fig3, use_container_width=True)

    anomaly_rows = agg_df[agg_df['anomaly'] == -1]
    if not anomaly_rows.empty:
        st.warning(
            f"Anomalous {time_scale.lower()} intervals: "
            f"{', '.join(str(t) for t in anomaly_rows['date_interval'])}"
        )
        st.dataframe(anomaly_rows[["date_interval", "error_count", "warning_count", "total_count"]], use_container_width=True)

        # Download anomalies to Excel
        output = io.BytesIO()
        anomaly_rows_for_excel = anomaly_rows.copy()
        anomaly_rows_for_excel["date_interval"] = anomaly_rows_for_excel["date_interval"].dt.tz_localize(None)
        with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
            anomaly_rows_for_excel.to_excel(writer, index=False, sheet_name="Anomalies")
        st.download_button(
            label="⬇️ Download Anomaly Intervals (Excel)",
            data=output.getvalue(),
            file_name="anomalies.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.success(f"No anomalies detected for selected date range/time scale.")
else:
    st.info("Not enough data for ML anomaly detection (need at least 5 intervals).")

# ---- Logs Pagination ----
st.markdown("---")
st.subheader("Log Viewer")
if not df.empty:
    page_size = st.selectbox("Logs per page", [10, 20, 50, 100, 200], index=2)
    total_logs = df.shape[0]
    total_pages = max((total_logs - 1) // page_size + 1, 1)
    page = st.number_input("Page", 1, total_pages, 1)
    start_idx = (page - 1) * page_size
    end_idx = min(start_idx + page_size, total_logs)
    st.markdown(f"Showing logs {start_idx + 1} to {end_idx} of {total_logs}")
    for i, row in df.iloc[start_idx:end_idx].iterrows():
        st.code(f"{row['datetime'].strftime('%Y-%m-%d %H:%M:%S')} [{row['level']}] {row['text']}", language="none")
else:
    st.info("No log lines for selected filter/search/date.")

st.caption("CloudWatch Log Dashboard · Powered by Streamlit · All times in IST.")


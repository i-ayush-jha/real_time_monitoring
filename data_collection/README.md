# Real-Time Application Error Prediction System

---

## 🚀 Overview

This project provides an **end-to-end, production-grade machine learning pipeline** for real-time error prediction and monitoring using AWS CloudWatch logs.  
It is designed for modern DevOps/SRE teams who want **early detection of anomalies and application errors** in web applications hosted on AWS EC2.

Key features include:

- **Automated log collection** from CloudWatch (via cron + Python)
- **Interactive Streamlit dashboard** with live log search, filtering, charts, and anomaly detection
- **ML-based anomaly detection** (Isolation Forest & heuristics)
- **Automated email alerts** for critical log events or anomalies
- **Download logs in TXT/Excel**
- **Secure, maintainable, and ready for handoff**

---

## 🏗️ High-Level Architecture

```mermaid
graph TD
    A[Web Application (Flask/Any App) on EC2] -->|Generates Logs| B[CloudWatch Logs]
    B -->|boto3 fetch| C[EC2 Python Script (fetch_cloudwatch_logs.py)]
    C -->|Appends| D[output_logs.txt]
    D -->|Reads| E[Streamlit Dashboard (dashboard.py)]
    E -->|User actions| F[DevOps / Engineer]
    E -->|Email/SMS alert| G[AWS SES/SNS]
    F -->|Triggers / receives alerts| G
    subgraph AWS Cloud
      A
      B
      C
      G
    end
    subgraph EC2 Instance
      D
      E
    end

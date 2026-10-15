import streamlit as st
import requests
import os

# API URL from Koyeb/Railway (will be set as env var)
API_URL = os.getenv("AGENT_API_URL", "http://localhost:8000")

st.set_page_config(page_title="AI Agent Control Panel", layout="wide")

st.title("🤖 AI Helper Agent Control Panel")

# Sidebar for Status
st.sidebar.header("System Status")
try:
    res = requests.get(f"{API_URL}/status").json()
    st.sidebar.success(f"Agent: {res['status']}")
except:
    st.sidebar.error("Agent: Offline")

# Main Area: Task Input
st.subheader("Assign New Task")
task = st.text_input("What should the agent do?")
if st.button("Launch Task"):
    if task:
        requests.post(f"{API_URL}/run", json={"task": task})
        st.info("Task sent! The agent is working in the background.")

# Reports Area
st.divider()
st.subheader("Recent Reports")
try:
    res = requests.get(f"{API_URL}/status").json()
    for report in reversed(res.get("last_reports", [])):
        with st.expander(f"Task: {report.get('task', 'Unknown')}"):
            if "result" in report:
                st.write(report["result"])
            else:
                st.error(report.get("error", "Unknown error"))
except Exception as e:
    st.write("No reports available yet.")

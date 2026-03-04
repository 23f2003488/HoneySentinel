import os
import streamlit as st
from openai import AzureOpenAI
from dotenv import load_dotenv
import matplotlib.pyplot as plt
from datetime import datetime

from agents.scout import scout_agent
from agents.hunter import hunter_agent
from agents.guardian import guardian_agent
from agents.sentinel import sentinel_agent
from memory import SecurityMemory
from risk_engine import calculate_risk, generate_risk_insight
from storage import upload_report_to_blob, load_reports_from_blob

# ---------------- CONFIG ---------------- #

st.set_page_config(page_title="HoneySentinel", layout="wide")

load_dotenv()

client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    api_version="2024-02-15-preview",
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT")
)

deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT")

# ---------------- SESSION STATE ---------------- #

if "analysis_data" not in st.session_state:
    st.session_state.analysis_data = None

if "scan_history" not in st.session_state:
    try:
        st.session_state.scan_history = load_reports_from_blob()
    except:
        st.session_state.scan_history = []

# ---------------- HEADER ---------------- #

st.markdown("## 🍯 HoneySentinel")
st.caption("Multi-Agent AI Security Intelligence Platform")
st.markdown("---")

# ---------------- UPLOAD SECTION ---------------- #

uploaded_file = st.file_uploader("Upload Python File", type=["py"])

if uploaded_file:
    code_content = uploaded_file.read().decode("utf-8")
    st.code(code_content, language="python")

    if st.button("🔍 Analyze Now"):

        memory = SecurityMemory()
        status = st.empty()

        # SCOUT
        status.info("🛰 Scout Agent analyzing structure...")
        scout_output = scout_agent(client, deployment_name, code_content)
        memory.log("Scout", "Structure analysis completed")

        # HUNTER
        status.info("🎯 Hunter Agent detecting vulnerabilities...")
        hunter_output = hunter_agent(client, deployment_name, scout_output)
        memory.log("Hunter", "Vulnerability detection completed")

        # GUARDIAN
        status.info("🛡 Guardian Agent validating findings...")
        guardian_output = guardian_agent(client, deployment_name, hunter_output)
        memory.log("Guardian", "Validation completed")

        # RISK ENGINE
        risk_data = calculate_risk(guardian_output)
        memory.log("RiskEngine", "Risk score calculated")

        # SENTINEL
        status.info("📄 Sentinel Agent generating report...")
        final_report = sentinel_agent(client, deployment_name, guardian_output)
        memory.log("Sentinel", "Final report generated")

        # EXECUTIVE INSIGHT
        insight = generate_risk_insight(
            client, deployment_name, risk_data, guardian_output
        )

        status.success("✅ Analysis Completed")

        # Store current scan
        current_scan = {
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "file_name": uploaded_file.name,
            "risk_score": risk_data["risk_score"],
            "risk_level": risk_data["risk_level"],
            "data": {
                "guardian_output": guardian_output,
                "risk_data": risk_data,
                "final_report": final_report,
                "insight": insight,
                "trace": memory.get_trace()
            }
        }

        blob_filename = f"{uploaded_file.name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        upload_report_to_blob(current_scan, blob_filename)

        st.session_state.analysis_data = current_scan["data"]
        st.session_state.scan_history.append(current_scan)

# ---------------- RESULTS SECTION ---------------- #

st.markdown("---")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    ["📊 Dashboard", "🔎 Vulnerabilities", "📄 Report", "🧠 Trace", "📁 History", "🔒 Security & Privacy"]
)

# ---------------- DASHBOARD ---------------- #

with tab1:

    if not st.session_state.analysis_data:
        st.info("No scan available. Upload a file to begin analysis.")
    else:
        data = st.session_state.analysis_data
        risk_data = data["risk_data"]
        guardian_output = data["guardian_output"]
        vulns = guardian_output.get("validated_vulnerabilities", [])

        col1, col2, col3 = st.columns(3)
        col1.metric("Risk Score", f"{risk_data['risk_score']} / 100")
        col2.metric("Risk Level", risk_data["risk_level"])
        col3.metric("Confidence", f"{risk_data['confidence']}%")

        st.markdown("### Severity Distribution")

        severity_counts = {"Low": 0, "Medium": 0, "High": 0, "Critical": 0}

        for v in vulns:
            severity = v.get("severity", "Low")
            if severity in severity_counts:
                severity_counts[severity] += 1

        fig, ax = plt.subplots(figsize=(4, 2))
        ax.bar(severity_counts.keys(), severity_counts.values())
        ax.set_xlabel("")
        ax.set_ylabel("")
        ax.set_title("")
        ax.tick_params(axis='both', which='both', length=0)
        plt.tight_layout()

        st.pyplot(fig, width="content")

        st.markdown("### 🧠 Executive Insight")
        st.write(data["insight"])

# ---------------- VULNERABILITIES ---------------- #

with tab2:

    if not st.session_state.analysis_data:
        st.info("No vulnerabilities to display yet.")
    else:
        vulns = st.session_state.analysis_data["guardian_output"].get(
            "validated_vulnerabilities", []
        )

        if not vulns:
            st.success("No validated vulnerabilities found.")
        else:
            for v in vulns:
                with st.expander(f"{v['type']} ({v['severity']})"):
                    st.write(v["reason"])

# ---------------- REPORT ---------------- #

with tab3:

    if not st.session_state.analysis_data:
        st.info("No report generated yet.")
    else:
        st.write(st.session_state.analysis_data["final_report"])

# ---------------- TRACE ---------------- #

with tab4:

    if not st.session_state.analysis_data:
        st.info("No execution trace available yet.")
    else:
        st.json(st.session_state.analysis_data["trace"])

# ---------------- HISTORY ---------------- #

with tab5:

    if not st.session_state.scan_history:
        st.info("No previous scans available.")
    else:
        for idx, scan in enumerate(reversed(st.session_state.scan_history)):

            col1, col2, col3, col4 = st.columns([3, 1, 1, 2])

            col1.write(f"**{scan['file_name']}**")
            col2.write(scan["risk_score"])
            col3.write(scan["risk_level"])
            col4.write(scan["timestamp"])

            if st.button("View", key=f"view_{idx}"):
                st.session_state.analysis_data = scan["data"]
                st.rerun()

            st.markdown("---")

# ---------------- SECURITY & PRIVACY ---------------- #

with tab6:

    st.markdown("## 🔒 Security & Privacy Architecture")

    st.markdown("""
    **Data Handling Model**
    - Code is processed in-memory during analysis.
    - No permanent storage unless persistence is enabled.
    - Scan history is session-based by default.
    """)

    st.markdown("""
    **Azure Enterprise Security**
    - Powered by Azure OpenAI Service.
    - No training on customer data.
    - Encrypted HTTPS communication.
    - Designed for private Azure VNet deployment.
    """)

    st.success("HoneySentinel follows enterprise security-first principles.")
import os
import json
import streamlit as st
from openai import AzureOpenAI
from dotenv import load_dotenv
import matplotlib.pyplot as plt
from datetime import datetime

from agents.scout import scout_agent
from agents.hunter import hunter_agent
from agents.guardian import guardian_agent
from agents.sentinel import sentinel_agent
from core.memory import SecurityMemory
from core.risk_engine import calculate_risk, generate_risk_insight
from storage.storage import upload_report_to_blob, load_reports_from_blob
from core.repo_scanner import scan_github_repo

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

if "repo_code" not in st.session_state:
    st.session_state.repo_code = None

if "repo_name" not in st.session_state:
    st.session_state.repo_name = None

if "scan_history" not in st.session_state:
    try:
        st.session_state.scan_history = load_reports_from_blob()
    except:
        st.session_state.scan_history = []

# ---------------- ANALYSIS FUNCTION ---------------- #

def run_analysis(code_content, file_name):

    memory = SecurityMemory()
    status = st.empty()

    # ---------------- SCOUT & HUNTER PIPELINE ---------------- #
    vulnerabilities = []

    if isinstance(code_content, dict):
        total_files = len(code_content)
        progress = st.progress(0)

        for idx, (fname, code) in enumerate(code_content.items()):
            
            # 1. Scout parses the raw code
            status.info(f"🛰 Scout Agent analyzing structure of {fname}...")
            scout_output = scout_agent(client, deployment_name, code)
            memory.log("Scout", f"Structure analysis completed for {fname}")

            # 2. Hunter uses Scout's structured JSON
            status.info(f"🎯 Hunter Agent detecting vulnerabilities in {fname}...")
            hunter_output = hunter_agent(client, deployment_name, scout_output)

            if hunter_output and isinstance(hunter_output, dict) and "vulnerabilities" in hunter_output:
                for v in hunter_output["vulnerabilities"]:
                    v["file"] = fname
                    vulnerabilities.append(v)

            progress.progress((idx + 1) / total_files)

    else:
        # Single file flow
        status.info("🛰 Scout Agent analyzing structure...")
        scout_output = scout_agent(client, deployment_name, code_content)
        memory.log("Scout", "Structure analysis completed")

        status.info("🎯 Hunter Agent detecting vulnerabilities...")
        hunter_output = hunter_agent(client, deployment_name, scout_output)

        if hunter_output and isinstance(hunter_output, dict):
            vulnerabilities = hunter_output.get("vulnerabilities", [])
            for v in vulnerabilities:
                v["file"] = file_name
        
    memory.log("Hunter", "Vulnerability detection completed")
    hunter_result = {"vulnerabilities": vulnerabilities}

    # ---------------- GUARDIAN ---------------- #

    status.info("🛡 Guardian Agent validating findings...")

    # Fixed: Passing dictionary directly to avoid double JSON encoding
    guardian_output = guardian_agent(
        client,
        deployment_name,
        hunter_result
    )

    validated = guardian_output.get("validated_vulnerabilities", [])

    # Fixed: Matching vulnerabilities by type to preserve file names
    for v in validated:
        original = next((orig for orig in vulnerabilities if orig.get("type") == v.get("type")), None)
        if original and "file" in original:
            v["file"] = original["file"]

    memory.log("Guardian", "Validation completed")

    # ---------------- RISK ENGINE ---------------- #

    risk_data = calculate_risk(guardian_output)

    memory.log("RiskEngine", "Risk score calculated")

    # ---------------- SENTINEL ---------------- #

    status.info("📄 Sentinel Agent generating report...")

    final_report = sentinel_agent(client, deployment_name, guardian_output)

    memory.log("Sentinel", "Final report generated")

    insight = generate_risk_insight(
        client,
        deployment_name,
        risk_data,
        guardian_output
    )

    status.success("✅ Analysis Completed")

    # ---------------- SAVE RESULT ---------------- #

    current_scan = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "file_name": file_name,
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

    blob_filename = f"{file_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    try:
        upload_report_to_blob(current_scan, blob_filename)
    except Exception as e:
        st.warning(f"Could not upload to blob storage: {e}")

    st.session_state.analysis_data = current_scan["data"]
    st.session_state.scan_history.append(current_scan)

# ---------------- HEADER ---------------- #

st.markdown("## 🍯 HoneySentinel")
st.caption("Multi-Agent AI Security Intelligence Platform")
st.markdown("---")

# ---------------- REPO INPUT ---------------- #

st.markdown("### Analyze GitHub Repository")

repo_url = st.text_input("Enter GitHub Repository URL")

if repo_url and st.button("Clone & Analyze Repo"):

    with st.spinner("Cloning repository and extracting Python files..."):

        try:

            repo_files = scan_github_repo(repo_url)
            repo_name = repo_url.rstrip("/").split("/")[-1]

            st.session_state.repo_code = repo_files
            st.session_state.repo_name = repo_name

            st.success("Repository cloned successfully!")
            run_analysis(repo_files, repo_name)

        except Exception as e:
            st.error(f"Failed to process repository: {e}")

st.markdown("---")

# ---------------- FILE INPUT ---------------- #

uploaded_file = st.file_uploader("Upload Python File", type=["py"])

if uploaded_file:

    code_content = uploaded_file.read().decode("utf-8")
    file_name = uploaded_file.name

    st.code(code_content, language="python")

    if st.button("🔍 Analyze Now"):
        run_analysis(code_content, file_name)

# ---------------- RESULTS ---------------- #

st.markdown("---")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    ["📊 Dashboard", "🔎 Vulnerabilities", "📄 Report", "🧠 Trace", "📁 History", "🔒 Security & Privacy"]
)

# ---------------- DASHBOARD ---------------- #

with tab1:

    if not st.session_state.analysis_data:
        st.info("No scan available. Upload a file or analyze a repository.")
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

        fig, ax = plt.subplots(figsize=(4,2))
        ax.bar(severity_counts.keys(), severity_counts.values())
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

                title = f"{v['type']} ({v['severity']})"

                if "file" in v:
                    title += f" — {v['file']}"

                with st.expander(title):
                    st.write(v.get("reason", "No reason provided."))

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
        sorted_history = sorted(
            st.session_state.scan_history,
            key=lambda x: datetime.strptime(x["timestamp"], "%Y-%m-%d %H:%M:%S"),
            reverse=True
        )

        header1, header2, header3, header4 = st.columns([3,1,1,2])

        header1.markdown("**File**")
        header2.markdown("**Score**")
        header3.markdown("**Risk**")
        header4.markdown("**Timestamp**")

        st.markdown("---")

        for idx, scan in enumerate(sorted_history):

            col1, col2, col3, col4 = st.columns([3,1,1,2])

            col1.write(f"**{scan['file_name']}**")
            col2.write(scan["risk_score"])
            col3.write(scan["risk_level"])
            col4.write(scan["timestamp"])

            if st.button("View", key=f"view_{idx}"):
                st.session_state.analysis_data = scan["data"]
                st.rerun()

            st.markdown("---")

# ---------------- SECURITY ---------------- #

with tab6:

    st.markdown("## 🔒 Security & Privacy Architecture")

    st.markdown("""
**Data Handling Model**

- Code processed in-memory
- Reports stored securely in Azure Blob Storage
- Private container access
""")

    st.markdown("""
**Azure Security**

- Azure OpenAI Service
- Encrypted HTTPS
- No model training on customer data
""")

    st.success("HoneySentinel follows enterprise security-first principles.")
import os
import json
import streamlit as st
from openai import AzureOpenAI
from dotenv import load_dotenv
import plotly.express as px
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
    
    # 🌟 NEW: Live Terminal UI (st.status)
    with st.status(f"🚀 Initializing scan for {file_name}...", expanded=True) as status_box:

        # ---------------- SCOUT, HUNTER & GUARDIAN PIPELINE ---------------- #
        all_validated_vulnerabilities = []

        if isinstance(code_content, dict):
            total_files = len(code_content)
            progress = st.progress(0)

            for idx, (fname, code) in enumerate(sorted(code_content.items())):
                
                st.write(f"🛰️ Scout Agent analyzing structure of {fname}...")
                scout_output = scout_agent(client, deployment_name, code, file_name=fname)
                inputs = len(scout_output.get("user_inputs", []))
                sinks = len(scout_output.get("dangerous_calls", []))
                memory.log("Scout", f"Mapped attack surface for {fname}: Identified {inputs} user inputs and {sinks} dangerous calls.", status="INFO")

                st.write(f"🎯 Hunter Agent detecting vulnerabilities in {fname}...")
                hunter_output = hunter_agent(client, deployment_name, scout_output, file_name=fname)

                if hunter_output and hunter_output.get("vulnerabilities"):
                    found_count = len(hunter_output["vulnerabilities"])
                    memory.log("Hunter", f"Analyzed {fname}: Flagged {found_count} potential flaws.", status="WARNING")
                    
                    st.write(f"🛡️ Guardian Agent validating {fname}...")
                    guardian_output = guardian_agent(client, deployment_name, hunter_output)
                    valid_vulns = guardian_output.get("validated_vulnerabilities", [])
                    all_validated_vulnerabilities.extend(valid_vulns)
                    
                    dropped = found_count - len(valid_vulns)
                    memory.log("Guardian", f"Triage {fname}: Dropped {dropped} false positives. Confirmed {len(valid_vulns)} threats.", status="SUCCESS")
                else:
                    memory.log("Hunter", f"Analyzed {fname}: No vulnerabilities detected.", status="SUCCESS")

                progress.progress((idx + 1) / total_files)
            
            # Combine all file results for the Risk Engine
            guardian_output = {"validated_vulnerabilities": all_validated_vulnerabilities}

        else:
            # Single file flow
            st.write(f"🛰️ Scout Agent analyzing structure of {file_name}...")
            scout_output = scout_agent(client, deployment_name, code_content, file_name=file_name)
            inputs = len(scout_output.get("user_inputs", []))
            sinks = len(scout_output.get("dangerous_calls", []))
            memory.log("Scout", f"Mapped attack surface for {file_name}: Identified {inputs} inputs and {sinks} dangerous calls.", status="INFO")

            st.write(f"🎯 Hunter Agent detecting vulnerabilities in {file_name}...")
            hunter_output = hunter_agent(client, deployment_name, scout_output, file_name=file_name)

            if hunter_output and hunter_output.get("vulnerabilities"):
                found_count = len(hunter_output["vulnerabilities"])
                memory.log("Hunter", f"Analyzed {file_name}: Flagged {found_count} potential flaws.", status="WARNING")
                
                st.write("🛡️ Guardian Agent validating findings...")
                guardian_output = guardian_agent(client, deployment_name, hunter_output)
                valid_vulns = guardian_output.get("validated_vulnerabilities", [])
                
                dropped = found_count - len(valid_vulns)
                memory.log("Guardian", f"Triage complete: Dropped {dropped} false positives. Confirmed {len(valid_vulns)} threats.", status="SUCCESS")
            else:
                guardian_output = {"validated_vulnerabilities": []}
                memory.log("Hunter", f"Analyzed {file_name}: No vulnerabilities detected.", status="SUCCESS")

        # ---------------- RISK ENGINE ---------------- #
        st.write("🧮 Calculating risk metrics...")
        risk_data = calculate_risk(guardian_output)
        memory.log("RiskEngine", "Risk score calculated", status="SUCCESS")

        # ---------------- SENTINEL ---------------- #
        st.write("📄 Sentinel Agent generating report...")
        final_report = sentinel_agent(client, deployment_name, guardian_output)
        memory.log("Sentinel", "Final report generated", status="SUCCESS")

        st.write("🧠 Generating executive insight...")
        insight = generate_risk_insight(client, deployment_name, risk_data, guardian_output)

        # Collapse the terminal when finished
        status_box.update(label="✅ Analysis Completed", state="complete", expanded=False)

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

# ---------------- INPUT TOGGLE ---------------- #

st.markdown("### Select Scan Target")
scan_mode = st.radio("Choose input method:", ["GitHub Repository", "Single Python File"], horizontal=True)

st.markdown("---")

if scan_mode == "GitHub Repository":
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

elif scan_mode == "Single Python File":
    uploaded_file = st.file_uploader("Upload Python File", type=["py"])

    if uploaded_file:
        code_content = uploaded_file.read().decode("utf-8")
        file_name = uploaded_file.name

        st.code(code_content, language="python")

        if st.button("🔍 Analyze Now"):
            # Clear old repository data from memory
            st.session_state.repo_code = None
            st.session_state.repo_name = None
            run_analysis(code_content, file_name)

# ---------------- RESULTS ---------------- #

st.markdown("---")

tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(
    ["📊 Dashboard", "🔎 Vulnerabilities", "📄 Report", "🧠 AI Audit Trail", "📁 History", "🔒 Security & Privacy"]
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

        fig = px.bar(
            x=list(severity_counts.keys()),
            y=list(severity_counts.values()),
            color=list(severity_counts.keys()),
            text=list(severity_counts.values()), # Add the numbers directly to the bars
            color_discrete_map={
                "Low": "#10B981",      # Vibrant Emerald
                "Medium": "#F59E0B",   # Vibrant Amber
                "High": "#EA580C",     # Deep Orange
                "Critical": "#EF4444"  # Punchy Red
            },
            labels={"x": "", "y": "Count"}
        )
        
        # Style the bars and tooltip
        fig.update_traces(
            textposition='outside', # Put numbers above the bars
            textfont=dict(size=16, color="white"),
            hovertemplate="<b>%{x} Severity</b><br>Count: %{y}<extra></extra>",
            cliponaxis=False # Prevent top numbers from getting cut off
        )

        # Strip away all the visual noise
        fig.update_layout(
            showlegend=False, 
            margin=dict(l=10, r=10, t=30, b=10), 
            height=300,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            xaxis=dict(
                showgrid=False, 
                zeroline=False,
                tickfont=dict(size=14, weight='bold') # Bold the X-axis text
            ),
            yaxis=dict(
                showgrid=True, 
                gridcolor="rgba(255,255,255,0.05)", # Extremely subtle grid
                zeroline=False,
                showticklabels=False # Hide the side numbers for a cleaner look
            )
        )

        st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

        st.markdown("### 🧠 Executive Insight")
        st.write(data["insight"])

       # ---------------- FILE RISK MAP ---------------- #

        st.markdown("### 📂 Security Map")

        file_risk = {}

        if st.session_state.repo_code and isinstance(st.session_state.repo_code, dict):
            for f in st.session_state.repo_code.keys():
                file_risk[f] = "🟢 Safe"

        for v in vulns:
            file = v.get("file")
            severity = v.get("severity", "Low")

            if not file:
                continue

            if severity == "Critical":
                file_risk[file] = "🔴 Critical"
            elif severity == "High":
                if file_risk.get(file) != "🔴 Critical":
                    file_risk[file] = "🟠 High"
            elif severity == "Medium":
                if file_risk.get(file) not in ["🔴 Critical", "🟠 High"]:
                    file_risk[file] = "🟡 Medium"

        for file, risk in sorted(file_risk.items()):
            st.write(f"**{file}** — {risk}")

# ---------------- VULNERABILITIES ---------------- #

with tab2:

    if not st.session_state.analysis_data:
        st.info("No vulnerabilities to display yet.")
    else:
        vulns = st.session_state.analysis_data["guardian_output"].get("validated_vulnerabilities", [])

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
        # 🌟 NEW: Styled terminal trace utilizing the memory status updates
        st.markdown("### Agent Execution Log")
        for trace in st.session_state.analysis_data["trace"]:
            icon = "🟢" if trace.get("status") == "SUCCESS" else "🔴" if trace.get("status") == "ERROR" else "🔵"
            st.write(f"{icon} **{trace['time']} | {trace['agent']}** — {trace['message']}")

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

**Azure Security**
- Azure OpenAI Service
- Encrypted HTTPS
- No model training on customer data
""")
    st.success("HoneySentinel follows enterprise security-first principles.")
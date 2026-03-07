# 🍯 HoneySentinel

### Multi-Agent AI Security Analyzer

HoneySentinel is an **AI-powered multi-agent security analysis platform** that automatically detects vulnerabilities in Python codebases and GitHub repositories.

Built for **Microsoft AI Unlocked Hackathon**, HoneySentinel demonstrates how **collaborating AI agents** can analyze code structure, detect vulnerabilities, validate findings, and generate security reports.

---

# 🚀 Features

### 🔍 Code Vulnerability Detection

Upload a Python file or scan an entire GitHub repository to detect security issues such as:

* Code Injection
* Unsafe `eval()` usage
* Insecure input handling
* Potential privilege escalation
* Risky code patterns

---

### 🤖 Multi-Agent AI Architecture

HoneySentinel uses a **collaborative agent workflow** where each AI agent performs a specialized task:

| Agent              | Role                                                      |
| ------------------ | --------------------------------------------------------- |
| **Scout Agent**    | Analyzes code structure and extracts relevant information |
| **Hunter Agent**   | Detects potential vulnerabilities                         |
| **Guardian Agent** | Validates and filters false positives                     |
| **Risk Engine**    | Calculates risk score and severity                        |
| **Sentinel Agent** | Generates a detailed security report                      |

Pipeline:

```
Code / Repository
        ↓
Scout Agent
        ↓
Hunter Agent
        ↓
Guardian Agent
        ↓
Risk Engine
        ↓
Sentinel Agent
```

---

# 📂 Supported Inputs

HoneySentinel currently supports:

### 1️⃣ Single File Analysis

Upload a `.py` file and analyze vulnerabilities instantly.

### 2️⃣ GitHub Repository Analysis

Paste a GitHub repository URL and HoneySentinel will:

1. Clone the repository
2. Extract Python files
3. Run AI vulnerability analysis per file
4. Generate a unified security report

---

# 📊 Dashboard Insights

HoneySentinel provides a visual security dashboard including:

* Risk Score
* Risk Level
* Confidence Score
* Vulnerability Severity Distribution
* Executive Risk Insight

---

# 🧠 Executive AI Security Insight

HoneySentinel also generates a **high-level executive security summary** to help teams quickly understand:

* Overall system risk
* Key vulnerabilities
* Immediate mitigation actions

---

# ☁️ Azure Integration

HoneySentinel is built using Microsoft AI infrastructure.

### Azure Services Used

| Service            | Purpose                    |
| ------------------ | -------------------------- |
| Azure OpenAI       | LLM-powered agent analysis |
| Azure Blob Storage | Security report storage    |
| Azure for Students | Cloud infrastructure       |

All communication is secured via **HTTPS** and reports are stored in **private blob containers**.

---

# 🏗️ Architecture

```
                +--------------------+
                |   User Interface   |
                |     (Streamlit)    |
                +----------+---------+
                           |
                           v
               +----------------------+
               |   HoneySentinel AI   |
               |  Multi-Agent Engine  |
               +----------------------+
                 |    |     |     |
                 v    v     v     v
               Scout Hunter Guardian Sentinel
                     |
                     v
               Risk Scoring Engine
                     |
                     v
               Security Report
                     |
                     v
            Azure Blob Storage
```

---

# 🛠️ Tech Stack

* **Python**
* **Streamlit**
* **Azure OpenAI**
* **Matplotlib**
* **GitPython**
* **Azure Blob Storage**

---

# 📦 Installation

### 1️⃣ Clone the Repository

```
git clone https://github.com/your-username/honeysentinel.git
cd honeysentinel
```

---

### 2️⃣ Install Dependencies

```
pip install -r requirements.txt
```

---

### 3️⃣ Setup Environment Variables

Create a `.env` file:

```
AZURE_OPENAI_API_KEY=your_key
AZURE_OPENAI_ENDPOINT=your_endpoint
AZURE_OPENAI_DEPLOYMENT=gpt-4o
```

---

### 4️⃣ Run the Application

```
streamlit run app.py
```

---

# 🧪 Example Usage

### Analyze Python File

Upload a Python file:

```
test.py
```

Example vulnerable code:

```python
user_input = input("Enter something: ")
eval(user_input)
```

HoneySentinel detects:

```
Code Injection Risk
Severity: High
```

---

### Analyze GitHub Repository

Paste repository URL:

```
https://github.com/user/repo
```

HoneySentinel will:

* clone repo
* analyze Python files
* generate security report

---

# 🔐 Security Philosophy

HoneySentinel follows **defensive security principles**:

* No training on user code
* Secure cloud storage
* Read-only repository scanning
* Transparent vulnerability reasoning

---

# 📈 Future Improvements

Planned upgrades:

* Dependency vulnerability detection
* AI exploit simulation
* Security heatmaps
* Authentication & user accounts
* CI/CD integration
* Real-time repository monitoring

---

# 🏆 Built For

**Microsoft AI Unlocked Hackathon**

---

# 👨‍💻 Author

Priyanshu Agarwal
IIT Madras – BS in Data Science

---

# 📜 License

MIT License

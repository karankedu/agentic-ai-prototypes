# 🏦 HCM Self-Service Assistant

> **AI-powered HR Self-Service chatbot for the Human Capital Management (HCM) domain in banking — built with LangGraph multi-agent architecture and GPT-4o.**

![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python&logoColor=white)
![LangGraph](https://img.shields.io/badge/LangGraph-0.2+-green?logo=chainlink&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-412991?logo=openai&logoColor=white)
![Streamlit](https://img.shields.io/badge/Streamlit-1.35+-FF4B4B?logo=streamlit&logoColor=white)
![uv](https://img.shields.io/badge/uv-package%20manager-DE5FE9)
![License](https://img.shields.io/badge/License-MIT-yellow)

---

## 📌 Problem Statement

HR teams in large banks handle thousands of employee queries per month — leave requests, policy clarifications, training enrollments, and directory lookups. The majority of these are repetitive, self-serviceable tasks that still require human intervention because legacy HRMS portals (SAP HCM, Oracle HCM, Workday) offer poor UX and no conversational interface.

This POC demonstrates how a **multi-agent GenAI system** can automate the majority of those interactions, reduce HR helpdesk call volume by 30–40%, and provide employees with an instant, 24/7 self-service experience — while maintaining full audit trails required by banking regulators.

---

## ✨ What Employees Can Do

Interact in plain English — no forms, no menus, no ticket numbers:

| 🗂️ Capability | 💬 Example Queries |
|---|---|
| **Leave Management** | *"Check my annual leave balance"*, *"Apply for 3 days off from June 2–4"*, *"Cancel request LR-2026-0003"* |
| **Training & L&D** | *"Show mandatory compliance courses"*, *"Enrol me in the Python for Finance workshop"*, *"What training am I enrolled in?"* |
| **HR Policy Q&A** | *"What's the maternity leave policy?"*, *"Can I work from home 3 days a week?"*, *"What are my AML/KYC obligations?"* |
| **Employee Directory** | *"Show my profile"*, *"Who is in the Compliance team?"*, *"Who does EMP007 report to?"* |

---

## 🏗️ Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                   Employee (Web Browser / CLI)              │
└──────────────────────────┬──────────────────────────────────┘
                           │  Natural Language
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                  Streamlit Web UI  /  CLI                   │
│     (injects [Employee ID: EMPXXX] context into prompt)     │
└──────────────────────────┬──────────────────────────────────┘
                           │
                           ▼
┌─────────────────────────────────────────────────────────────┐
│                    LangGraph Graph                          │
│                                                             │
│   START                                                     │
│     │                                                       │
│     ▼                                                       │
│  ┌──────────────────────────────────┐                       │
│  │  Supervisor Agent  (GPT-4o)      │                       │
│  │  Structured output → routing     │                       │
│  │  intent: leave_management        │                       │
│  │  next_agent: leave_agent         │                       │
│  └────┬──────┬──────┬──────┬────────┘                       │
│       │      │      │      │                                │
│       ▼      ▼      ▼      ▼                                │
│   Leave  Training Policy  Info                              │
│   Agent   Agent   Agent  Agent                              │
│     │       │       │      │                                │
│   Tools   Tools   Tools  Tools                              │
│  (read +  (enrol/ (search (dir-                             │
│  write)   cancel) policy) ectory)                           │
│     │       │       │      │                                │
│    CSV     CSV     CSV    CSV                               │
│                                                             │
│   Each agent loops: agent → tools → agent → END             │
└─────────────────────────────────────────────────────────────┘
```

### Why Multi-Agent?

A single LLM with all tools is simpler to build but brittle at scale. The supervisor-router pattern provides:

| Design Choice | Benefit |
|---|---|
| **Dedicated supervisor** | Intent classification is isolated — routing logic never contaminates task execution |
| **Principle of least privilege** | Leave agent cannot accidentally call training tools; policy agent is read-only |
| **Specialised system prompts** | Each agent has domain-specific instructions (e.g., leave agent knows date formats; policy agent cites policy names) |
| **Pydantic structured output** | Supervisor returns validated JSON — eliminates free-text parsing failures |
| **Agent ↔ Tool loops** | Each agent calls tools iteratively until the task is fully resolved, then hands off cleanly |
| **Audit trail by design** | All writes create timestamped records with IDs — meets banking compliance requirements |

---

## 🤖 Agent Responsibilities

### Supervisor Agent
- Receives every user message
- Classifies intent into: `leave_management` | `training` | `policy_query` | `employee_info`
- Routes to the correct specialist via `next_agent` field in state
- Uses `with_structured_output()` for zero-hallucination routing

### 📅 Leave Agent
Handles the full leave lifecycle for an employee:
- `get_leave_balance` — remaining days by leave type
- `get_leave_history` — all past/present requests
- `check_leave_balance_sufficient` — pre-flight check before submitting
- `submit_leave_request` — creates `LR-YYYY-XXXX` ID, deducts balance, appends to CSV
- `cancel_leave_request` — marks Cancelled, restores balance

### 🎓 Training Agent
Manages the learning catalog and enrollments:
- `list_available_trainings` — filtered by category, shows seat count
- `get_training_details` — full course info with mandatory flag
- `enroll_in_training` — prevents duplicates, decrements seat count
- `cancel_training_enrollment` — releases seat back to pool
- `get_my_training_enrollments` — active enrollments for an employee

### 📋 Policy Agent
Answers questions from the HR policy knowledge base:
- `search_hr_policy` — keyword search across title, content, and category
- `list_policy_categories` — all available policy buckets
- `get_policy_by_category` — full text of all policies in a category

### 👤 Info Agent
Read-only employee directory queries:
- `get_employee_info` — profile, designation, manager, location
- `list_employees_by_department` — all staff in a department

---

## 📁 Project Structure

```
hcm-self-service-assistant/
│
├── streamlit_app.py              ← Streamlit web UI with sidebar quick-actions
├── main.py                       ← CLI entry point with employee login
├── pyproject.toml                ← Dependencies (managed with uv)
├── .env.example                  ← Environment variable template
│
├── 📊 Data (CSV-backed, writable at runtime)
│   ├── employee_directory.csv        10 bank employees across 8 departments
│   ├── employee_leave_balances.csv   Leave entitlements & used days (2026)
│   ├── leave_requests.csv            Leave request history + new submissions
│   ├── training_sessions.csv         Training catalog with seat availability
│   ├── training_enrollments.csv      Per-employee enrollment records
│   └── hr_policies.csv              10 full HR policy documents
│
└── hcm_agent/                    ← Core Python package
    ├── config/
    │   └── settings.py               CSV paths, valid leave types, categories
    ├── models/
    │   └── state.py                  HCMState TypedDict (LangGraph state)
    ├── utils.py                      sanitize_messages() — defensive LLM guard
    ├── logging_config.py             Rotating file + console logger
    ├── tools/
    │   ├── leave_reader.py           3 read tools for leave queries
    │   ├── leave_writer.py           2 write tools (submit, cancel)
    │   ├── training_tools.py         5 tools (list, details, enrol, cancel, mine)
    │   ├── policy_tools.py           3 tools (search, categories, by-category)
    │   └── employee_tools.py         2 tools (profile, by-department)
    └── workflows/
        └── graph.py                  Full LangGraph graph — supervisor + 4 agents
```

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/getting-started/installation/) package manager
- OpenAI API key with GPT-4o access

### 1 — Clone & configure

```bash
git clone https://github.com/karankedu/genai-architect-sandbox.git
cd genai-architect-sandbox/hcm-self-service-assistant

# Copy the env template and add your API key
cp .env.example .env
```

Edit `.env`:
```env
OPENAI_API_KEY=sk-...your-key-here...
MODEL_NAME=gpt-4o
TEMPERATURE=0
```

### 2 — Install dependencies

```bash
uv sync
```

### 3 — Launch the Streamlit UI

```bash
uv run streamlit run streamlit_app.py
```

Opens at **http://localhost:8501**

### 4 — Or use the CLI

```bash
uv run python main.py
```

---

## 🎭 Demo Script (Interview Ready)

Run these in sequence to exercise all 4 agents live. Use Employee ID **EMP001** (Rahul Sharma, Retail Banking Analyst):

```
Step 1 — Leave Agent (read)
  "Check my leave balance"
  ✓ Shows annual / sick / emergency / paternity remaining days

Step 2 — Leave Agent (write)
  "I want to apply for 2 days annual leave from 2026-06-09 to 2026-06-10"
  ✓ Submits request, returns LR-2026-XXXX ID, deducts from balance

Step 3 — Leave Agent (read → cancel)
  "Show my leave history"  →  then  "Cancel request LR-2026-0001"
  ✓ Lists history, then cancels and restores 5 days to balance

Step 4 — Training Agent (browse mandatory)
  "Show me mandatory compliance training courses"
  ✓ Lists AML/KYC, Cybersecurity, Data Privacy — with seat counts

Step 5 — Training Agent (enrol)
  "Enrol me in TRN003"
  ✓ Enrolls in Python for Finance, decrements available seats

Step 6 — Policy Agent
  "What is the maternity leave policy?"
  ✓ Retrieves and summarises the full Maternity & Paternity Leave Policy

Step 7 — Policy Agent (compliance)
  "As a bank employee, what are my AML and KYC obligations?"
  ✓ Returns AML/KYC Compliance Policy with key obligations

Step 8 — Info Agent
  "Who is in the Compliance department?"
  ✓ Lists Amit Kumar (Manager) and Meera Iyer (Associate)

Step 9 — Training Agent (cancel)
  "Cancel my enrollment in TRN003"
  ✓ Cancels, seat is released back to TRN003
```

After each response the UI shows a routing badge:
> 🔀 Routed to **📅 Leave Agent** · intent: `leave_management`

This visually demonstrates the supervisor routing the request to the right specialist.

---

## 📊 Mock Data

### Employees

| ID | Name | Department | Designation |
|---|---|---|---|
| EMP001 | Rahul Sharma | Retail Banking | Analyst |
| EMP002 | Priya Patel | Risk Management | Associate |
| EMP003 | Amit Kumar | Compliance | Manager |
| EMP004 | Sneha Reddy | IT Department | Analyst |
| EMP005 | Vikram Singh | HR | Senior Manager |
| EMP006 | Deepa Nair | Retail Banking | Associate |
| EMP007 | Karan Mehta | Treasury | AVP |
| EMP008 | Ananya Gupta | Operations | Analyst |
| EMP009 | Rohit Joshi | Audit & Control | Manager |
| EMP010 | Meera Iyer | Compliance | Associate |

### Training Catalog (10 courses)

| ID | Course | Category | Mandatory |
|---|---|---|---|
| TRN001 | AML/KYC Refresher 2026 | `aml_kyc` | ✅ Yes |
| TRN002 | Basel III Capital Requirements | `risk_management` | ✅ Yes |
| TRN003 | Python for Finance & Banking | `technical_skills` | No |
| TRN004 | Leadership Excellence Program | `leadership_management` | No |
| TRN005 | Customer Centricity Workshop | `customer_service` | No |
| TRN006 | Data Privacy & GDPR Compliance | `compliance_regulatory` | ✅ Yes |
| TRN007 | Advanced Excel for Banking Analysts | `technical_skills` | No |
| TRN008 | Cybersecurity Awareness Training | `compliance_regulatory` | ✅ Yes |
| TRN009 | Conflict Resolution & Mediation | `leadership_management` | No |
| TRN010 | Financial Statement Analysis | `technical_skills` | No |

### HR Policies (10 documents)

| Category | Policies |
|---|---|
| Leave Management | Annual Leave, Sick Leave, Maternity & Paternity Leave |
| Work Arrangements | Work From Home Policy |
| Compliance | AML/KYC Compliance, Data Privacy & Information Security |
| Performance | Performance Management Policy |
| Conduct | Code of Conduct |
| Travel and Expense | Travel & Expense Policy |
| HR Processes | Grievance Redressal Policy |

---

## 🛠️ Tech Stack

| Technology | Version | Role |
|---|---|---|
| [LangGraph](https://langchain-ai.github.io/langgraph/) | ≥ 0.2 | Multi-agent orchestration, state machine, tool loops |
| [LangChain OpenAI](https://python.langchain.com/docs/integrations/chat/openai/) | ≥ 0.2 | GPT-4o chat + structured output |
| [OpenAI](https://platform.openai.com/) | ≥ 1.0 | LLM provider (GPT-4o) |
| [Streamlit](https://streamlit.io/) | ≥ 1.35 | Interactive web UI |
| [Pydantic](https://docs.pydantic.dev/) | ≥ 2.0 | Supervisor structured output, type safety |
| [Pandas](https://pandas.pydata.org/) | ≥ 2.0 | CSV read/write for all data operations |
| [uv](https://docs.astral.sh/uv/) | latest | Fast Python package & project management |
| [python-dotenv](https://pypi.org/project/python-dotenv/) | ≥ 1.0 | Environment variable loading |

---

## 🏦 HCM Domain Relevance for Banking

### Why this matters in a bank

| Pain Point | How This POC Addresses It |
|---|---|
| HR helpdesk overloaded with repetitive queries | 4 specialised agents handle the top query categories autonomously |
| Mandatory compliance training tracking (AML/KYC, Cybersecurity) | Training agent highlights mandatory courses; enrollment is tracked with audit records |
| Leave approval delays via email chains | Leave agent auto-approves and creates audit-trail records (LR-YYYY-XXXX IDs) |
| Employees can't find HR policies on intranet | Policy agent performs natural-language search across all policy documents |
| No self-service for simple data lookups | Info agent provides instant directory access without HRMS portal login |

### Industry Benchmarks
- **30–40%** reduction in HR helpdesk call volume from self-service chatbots *(Gartner, 2024)*
- **~25%** of HR tickets are policy clarification requests *(ServiceNow HR Benchmark)*
- **4–6 weeks** average time-to-resolve for HRMS customisation requests — AI layer avoids this entirely

---

## 🗺️ Production Roadmap

This is a CSV-backed prototype. Here is the path to a production-grade system:

```
POC (this repo)          →    Production
─────────────────────────────────────────────────────────────────
CSV files                →    SAP HCM / Oracle HCM / Workday API
Keyword policy search    →    RAG over SharePoint / Confluence
                               (vector DB: Azure AI Search / Pinecone)
Auto-approved leave      →    Manager approval workflow (email + Teams)
Streamlit UI             →    Microsoft Teams bot / ServiceNow Virtual Agent
Single-tenant CSV        →    Multi-tenant with employee auth (Azure AD / SSO)
No access control        →    Role-based tool access (managers see team data)
Manual CSV audit trail   →    Immutable event log (Azure Event Hub / Splunk)
GPT-4o (OpenAI)          →    Azure OpenAI (data residency + compliance)
No monitoring            →    LangSmith tracing + Azure Monitor dashboards
```

### Compliance Considerations for Banking Production
- **Data Privacy (DPDP / GDPR)** — employee PII must stay within approved cloud regions; Azure OpenAI enables this
- **Audit & Control** — every AI action (leave booked, enrollment made) must be immutable and attributable
- **Model Risk Management** — LLM outputs for write operations should have human-in-the-loop approval gates
- **Explainability** — supervisor routing decisions are logged, providing a clear audit trail of AI reasoning

---

## 🔑 Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `OPENAI_API_KEY` | ✅ Yes | — | Your OpenAI API key |
| `MODEL_NAME` | No | `gpt-4o` | LLM model name |
| `TEMPERATURE` | No | `0` | LLM temperature (0 = deterministic) |

---

## 📄 License

MIT — free to use, adapt, and extend.

---

> *This POC was built to demonstrate how LangGraph's multi-agent supervisor pattern can be applied to the HCM domain in banking. It is intentionally simple at the data layer (CSV) to keep the focus on the AI orchestration architecture.*

# 🤖 Agentic AI Prototypes

> A collection of production-quality **multi-agent AI prototypes** built with LangGraph, demonstrating how agentic GenAI systems can automate domain-specific workflows in enterprise settings.

Each project in this repository is a standalone, runnable POC with a Streamlit UI, realistic mock data, and a documented architecture — designed to be demo-ready for technical interviews and stakeholder presentations.

---

## 📦 Projects

### 🏦 [hcm-self-service-assistant](./hcm-self-service-assistant/)

**AI-powered HR Self-Service chatbot for the HCM domain in banking**

Employees interact in natural language to manage leave, enrol in training, query HR policies, and look up the employee directory — all routed through a LangGraph multi-agent supervisor.

| | |
|---|---|
| **Domain** | Human Capital Management (HCM) · Banking & Financial Services |
| **Agents** | Supervisor · Leave Agent · Training Agent · Policy Agent · Info Agent |
| **Tools** | 14 `@tool` functions across leave, training, policy, and directory data |
| **Stack** | LangGraph · GPT-4o · Streamlit · Pandas · Pydantic · uv |

→ [Full documentation](./hcm-self-service-assistant/README.md)

---

## 🏗️ Architecture Pattern

All prototypes in this collection follow the **LangGraph Supervisor-Router** pattern:

```
User Input
    │
    ▼
Supervisor Agent          ← classifies intent via structured output
    │
    ├──► Specialist Agent A  ←→  Tool Set A
    ├──► Specialist Agent B  ←→  Tool Set B
    └──► Specialist Agent N  ←→  Tool Set N
```

**Design principles applied consistently across all projects:**

- **Principle of least privilege** — each agent only has access to its own tools
- **Structured output routing** — Pydantic-validated supervisor decisions, no free-text parsing
- **Agent ↔ Tool loops** — agents iterate with tools until fully resolved, then exit cleanly
- **Audit trail by design** — all write operations create timestamped, ID-tagged records
- **Defensive message sanitization** — guards against empty-content API rejections

---

## 🛠️ Common Tech Stack

| Technology | Role |
|---|---|
| [LangGraph](https://langchain-ai.github.io/langgraph/) | Multi-agent orchestration, state management, conditional routing |
| [LangChain OpenAI](https://python.langchain.com/) | GPT-4o integration with tool binding and structured output |
| [Streamlit](https://streamlit.io/) | Rapid web UI for demos |
| [Pydantic](https://docs.pydantic.dev/) | Structured output validation |
| [Pandas](https://pandas.pydata.org/) | Lightweight CSV-backed data layer (replaceable with HRMS/DB APIs) |
| [uv](https://docs.astral.sh/uv/) | Fast Python package management |

---

## 🗺️ Roadmap

| Project | Domain | Status |
|---|---|---|
| `hcm-self-service-assistant` | HR / HCM · Banking | ✅ Complete |
| *(more coming)* | | 🔜 Planned |

---

## 📄 License

MIT — free to use, adapt, and extend for your own domain.

# 🗺️ Production Roadmap

> This document outlines the features and engineering work required to take prototypes in this repository from POC to production-grade systems in a banking / enterprise environment.
>
> Organised by theme and phased by priority. Items marked 🏦 are especially critical for regulated banking environments.

---

## Phase 1 — MVP to Pilot

*Core foundations needed before any real employee uses the system.*

### 🔐 Authentication & Authorisation

- [ ] **SSO / Azure AD login** — employees authenticate via corporate SSO; no separate credentials
- [ ] **Employee identity auto-injection** — `emp_id` derived from the SSO token, never typed manually
- [ ] **Role-based access control (RBAC)** — employees see only their own data; managers see their team; HR sees all
- [ ] **Session management** — timeout, token refresh, concurrent session handling
- [ ] **Privileged action confirmation** — write actions (submit leave, enrol in training) require an explicit confirmation step before execution

### 🤖 AI / LLM Infrastructure

- [ ] 🏦 **Azure OpenAI** — migrate from `api.openai.com` to Azure OpenAI Service for data residency, compliance, and enterprise SLA
- [ ] **Prompt versioning** — store system prompts in config / DB so they can be updated without code deployments
- [ ] **Fallback / escalation agent** — if the AI's confidence is low or the task is too complex, route to a human HR agent via a ServiceNow ticket

### 🔒 Security & Compliance

- [ ] 🏦 **PII redaction in logs** — strip employee names, IDs, and emails from LLM prompt logs before storage
- [ ] 🏦 **No PII to external LLM** — enforced by using Azure OpenAI (data stays in the bank's Azure tenant)
- [ ] **Input sanitization** — guard against prompt injection attacks (e.g., *"ignore instructions and…"*)
- [ ] **Output filtering** — block responses containing account numbers, salary figures, or PII of other employees
- [ ] **Data encryption** — all employee data encrypted at rest (AES-256) and in transit (TLS 1.3)

### 📊 Observability

- [ ] **Structured logging** — JSON logs with `emp_id`, `intent`, `agent`, `latency_ms`, `token_count` sent to Azure Monitor / Splunk
- [ ] **LangSmith tracing** — full trace of every LLM call, tool call, and routing decision; queryable by session ID
- [ ] **Latency alerting** — alert via PagerDuty / Teams if P95 response time exceeds 5 seconds

### 🔄 HR Workflow

- [ ] **Manager approval workflow** — leave requests trigger an approval notification (email / Teams) to the manager instead of auto-approving
- [ ] **HRMS read integration** — connect employee directory and leave balances to SAP HCM / Oracle HCM / Workday read APIs (replace CSV)

---

## Phase 2 — Pilot to Production

*Scale, harden, and open up additional channels.*

### 🏗️ Data Layer

- [ ] **Database backend** — PostgreSQL / Oracle DB for leave requests and training enrollments, with transactions and rollback support
- [ ] **HRMS write-back** — submit leave approvals and training enrollments back to the HRMS via API
- [ ] **HR Master Data sync** — real-time employee directory sync from Azure Active Directory
- [ ] **Leave calendar integration** — pull public and regional holidays from a calendar service to accurately count working days
- [ ] **Connection pooling & retries** — resilient DB connections with exponential backoff and circuit breakers

### 🤖 AI / LLM Infrastructure

- [ ] **RAG for policy search** — replace keyword CSV search with vector embeddings over SharePoint / Confluence policy documents (Azure AI Search or Pinecone)
- [ ] **Conversation memory** — persist conversation history across sessions in Redis / Cosmos DB so employees can resume where they left off
- [ ] **Multi-language support** — respond in the employee's preferred language (Hindi, Tamil, etc.)

### 💬 Channel Expansion

- [ ] **Microsoft Teams bot** — deploy as a Teams app so employees interact where they already work
- [ ] **ServiceNow Virtual Agent** — embed as a widget in the HR / IT self-service portal
- [ ] **Mobile PWA** — progressive web app for branch and non-desk employees

### ⚙️ Scalability & Reliability

- [ ] **Containerisation** — Dockerise the application; deploy on Kubernetes (AKS)
- [ ] **Horizontal scaling** — multiple app instances behind a load balancer
- [ ] **Rate limiting** — per-employee and per-department request throttling
- [ ] **Health & readiness probes** — `/health` and `/ready` endpoints for Kubernetes liveness checks
- [ ] **Disaster recovery** — multi-region deployment; RTO < 1 hour, RPO < 15 minutes

### 🧪 Testing & CI/CD

- [ ] **Unit tests** — test each tool function with mock DataFrames (pytest)
- [ ] **Agent integration tests** — test full graph runs with fixture messages; assert correct agent routing
- [ ] **LLM eval suite** — LangSmith evaluations for intent classification accuracy and tool call correctness
- [ ] **CI pipeline** — GitHub Actions: lint → test → build Docker image → push to Azure Container Registry
- [ ] **CD pipeline** — ArgoCD / Azure DevOps: staging promotion with approval gate before production
- [ ] **Canary deployments** — roll new model versions out to 5% of traffic before full promotion

### 🔒 Security & Compliance

- [ ] 🏦 **Immutable audit log** — every write action (leave booked, enrollment made) written to an append-only audit store (Azure Event Hub / Splunk)
- [ ] **Penetration testing** — regular security audits of the API and chat interface
- [ ] 🏦 **DPDP / GDPR compliance** — employee consent for AI processing, right-to-erasure support in conversation history
- [ ] **SOC 2 / ISO 27001 alignment** — access controls, audit trails, and incident response aligned with the bank's compliance framework

---

## Phase 3 — Scale & Expand

*New agents, deeper integrations, and full AI governance.*

### 🔄 New Agent Capabilities

- [ ] **Onboarding agent** — new joiner checklist: IT access setup, policy acknowledgements, buddy assignment, induction schedule
- [ ] **Offboarding agent** — clearance checklist, final settlement queries, exit interview scheduling, asset return tracking
- [ ] **Performance review agent** — goal tracking, appraisal reminders, rating queries, PIP status
- [ ] **Payroll & tax agent** — payslip retrieval, tax declaration queries, reimbursement status
- [ ] **Grievance agent** — raise and track HR grievances; auto-escalate to POSH Committee for harassment cases
- [ ] **Calendar integration** — auto-block Outlook calendar on approved leave; send training reminders

### 🤖 AI / LLM Infrastructure

- [ ] **Model versioning & A/B testing** — test new GPT model versions against current without full deployment
- [ ] **Async processing** — long-running tasks (bulk leave reports, training completion exports) handled asynchronously with status polling
- [ ] **Personalisation** — agent adapts tone and detail level based on employee's role and past interactions

### 💬 Channel Expansion

- [ ] **WhatsApp / SMS** — for non-desk employees (branch staff, operations) via Twilio
- [ ] **Email integration** — employees reply to leave approval emails and the agent processes the response
- [ ] **Voice interface** — IVR-style interaction for employees without desktop access

### 📊 Observability

- [ ] **Token usage & cost dashboards** — cost per session, per department, per month for finance reporting
- [ ] **User satisfaction tracking** — thumbs up/down on responses; CSAT score by intent category
- [ ] **Model drift monitoring** — alert if intent classification accuracy degrades over time

---

## 🏛️ AI Governance (Critical for Banking)

> These items are non-negotiable for any bank deploying AI in an employee-facing system.

- [ ] 🏦 **Model Risk Management (MRM) documentation** — document the model, its limitations, validation approach, and known failure modes (required by RBI / FCA guidelines on AI in BFSI)
- [ ] 🏦 **Human-in-the-loop for sensitive actions** — manager or HR confirmation required for maternity leave, emergency leave, and any action affecting payroll
- [ ] 🏦 **Explainability logging** — log the supervisor's `reasoning` field for every routing decision, creating a queryable AI audit trail
- [ ] **Bias & fairness testing** — verify that policy responses are consistent across gender, religion, location, and seniority
- [ ] **Incident response playbook** — documented process for when the agent gives incorrect information (e.g., wrong leave balance, wrong policy cited)
- [ ] **AI usage policy alignment** — align with the bank's internal AI governance policy and relevant regulatory guidance

---

## 📋 Priority Summary

```
Phase 1 — MVP to Pilot
  ✦ Azure AD SSO + RBAC
  ✦ Azure OpenAI (data residency)          ← blocker for any bank CISO approval
  ✦ HRMS read API integration
  ✦ Structured logging + LangSmith tracing
  ✦ Input sanitization + output filtering
  ✦ Manager approval workflow

Phase 2 — Pilot to Production
  ✦ RAG policy search (Azure AI Search)
  ✦ Microsoft Teams bot channel
  ✦ Immutable audit log
  ✦ Containerisation + Kubernetes (AKS)
  ✦ Unit + integration test suite + CI/CD pipeline

Phase 3 — Scale & Expand
  ✦ HRMS write-back APIs
  ✦ Onboarding / offboarding / performance agents
  ✦ Escalation agent → ServiceNow tickets
  ✦ Multi-language support
  ✦ Full MRM documentation + AI governance framework
```

---

> 💡 **The single most important item for a bank:** Azure OpenAI with data residency.
> Without it, no CISO will approve the system for production regardless of how good the functionality is.

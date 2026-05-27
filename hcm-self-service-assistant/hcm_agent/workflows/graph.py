"""LangGraph multi-agent supervisor graph for the HCM Self-Service Assistant.

Architecture
────────────
  START
    │
    ▼
  supervisor  ──routes──►  leave_agent    ◄──► leave_tools
                     │──►  training_agent ◄──► training_tools
                     │──►  policy_agent   ◄──► policy_tools
                     │──►  info_agent     ◄──► info_tools
                     └──►  END

The supervisor classifies intent using structured output (Pydantic model)
and sets `next_agent` in state.  Each specialist loops with its ToolNode
until no tool calls remain, then routes to END.
"""

import os
from typing import Literal

from dotenv import load_dotenv
from langchain_core.messages import SystemMessage
from langchain_openai import ChatOpenAI
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from pydantic import BaseModel

from hcm_agent.models.state import HCMState
from hcm_agent.utils import sanitize_messages

# ── Tools ──────────────────────────────────────────────────────────
from hcm_agent.tools.leave_reader import (
    check_leave_balance_sufficient,
    get_leave_balance,
    get_leave_history,
)
from hcm_agent.tools.leave_writer import cancel_leave_request, submit_leave_request
from hcm_agent.tools.training_tools import (
    cancel_training_enrollment,
    enroll_in_training,
    get_my_training_enrollments,
    get_training_details,
    list_available_trainings,
)
from hcm_agent.tools.policy_tools import (
    get_policy_by_category,
    list_policy_categories,
    search_hr_policy,
)
from hcm_agent.tools.employee_tools import get_employee_info, list_employees_by_department

load_dotenv()

# ── Shared LLM ─────────────────────────────────────────────────────
_llm = ChatOpenAI(
    model=os.getenv("MODEL_NAME", "gpt-4o"),
    temperature=float(os.getenv("TEMPERATURE", 0)),
)


# ══════════════════════════════════════════════════════════════════
# SUPERVISOR
# ══════════════════════════════════════════════════════════════════

_SUPERVISOR_PROMPT = """You are the routing supervisor for a bank's HR Self-Service AI assistant.

Your only job is to classify the employee's intent and route to the correct specialist agent.

Specialist agents and what they handle:
  • leave_agent     — leave balance queries, submitting / cancelling leave requests, leave history
  • training_agent  — browsing training courses, enrolling, cancelling enrollments, my enrollments
  • policy_agent    — HR policy questions (leave rules, WFH policy, code of conduct, AML, etc.)
  • info_agent      — employee directory lookups, department info, manager details

Route to END only for greetings or requests completely unrelated to HR.

Respond with a JSON object ONLY — no extra text:
{"intent": "<intent>", "next_agent": "<agent>", "reasoning": "<one sentence>"}

intent  values: leave_management | training | policy_query | employee_info | unknown
agent   values: leave_agent | training_agent | policy_agent | info_agent | END"""


class _SupervisorDecision(BaseModel):
    intent: Literal[
        "leave_management", "training", "policy_query", "employee_info", "unknown"
    ]
    next_agent: Literal[
        "leave_agent", "training_agent", "policy_agent", "info_agent", "END"
    ]
    reasoning: str


_supervisor_llm = _llm.with_structured_output(_SupervisorDecision)


def supervisor_node(state: HCMState) -> dict:
    messages = sanitize_messages(state["messages"])
    decision = _supervisor_llm.invoke(
        [SystemMessage(content=_SUPERVISOR_PROMPT)] + messages
    )
    return {"intent": decision.intent, "next_agent": decision.next_agent}


def _route_from_supervisor(state: HCMState) -> str:
    return state.get("next_agent", "END")


# ══════════════════════════════════════════════════════════════════
# LEAVE AGENT
# ══════════════════════════════════════════════════════════════════

_LEAVE_SYSTEM_PROMPT = """You are the Leave Management specialist for a bank's HR system.

You help employees with:
  • Checking leave balances (annual, sick, emergency, maternity, paternity)
  • Submitting leave requests
  • Cancelling leave requests
  • Viewing leave history

Important rules:
  - Leave type values: annual_leave, sick_leave, emergency_leave, maternity_leave, paternity_leave
  - Dates must be in YYYY-MM-DD format
  - Always check the balance before submitting a request
  - Confirm the details with the employee before taking any write action
  - After completing an action, provide a clear, friendly summary"""

_leave_tools    = [get_leave_balance, get_leave_history, check_leave_balance_sufficient,
                   submit_leave_request, cancel_leave_request]
_leave_tool_node = ToolNode(_leave_tools)
_leave_llm       = _llm.bind_tools(_leave_tools)


def leave_agent_node(state: HCMState) -> dict:
    messages = sanitize_messages(state["messages"])
    response = _leave_llm.invoke(
        [SystemMessage(content=_LEAVE_SYSTEM_PROMPT)] + messages
    )
    return {"messages": [response]}


def _leave_condition(state: HCMState) -> Literal["leave_tools", "__end__"]:
    last = state["messages"][-1]
    return "leave_tools" if getattr(last, "tool_calls", None) else "__end__"


# ══════════════════════════════════════════════════════════════════
# TRAINING AGENT
# ══════════════════════════════════════════════════════════════════

_TRAINING_SYSTEM_PROMPT = """You are the Training & Development specialist for a bank's HR system.

You help employees with:
  • Discovering available training sessions (with or without category filter)
  • Getting detailed course information
  • Enrolling in training courses
  • Cancelling training enrollments
  • Checking their current training enrollments

Important rules:
  - Always highlight MANDATORY compliance training (AML/KYC, cybersecurity, data privacy)
  - Mention deadlines for mandatory training when relevant
  - Confirm enrollment/cancellation actions before proceeding
  - Category values: aml_kyc, compliance_regulatory, risk_management,
                     technical_skills, leadership_management, customer_service"""

_training_tools    = [list_available_trainings, get_training_details, enroll_in_training,
                      cancel_training_enrollment, get_my_training_enrollments]
_training_tool_node = ToolNode(_training_tools)
_training_llm       = _llm.bind_tools(_training_tools)


def training_agent_node(state: HCMState) -> dict:
    messages = sanitize_messages(state["messages"])
    response = _training_llm.invoke(
        [SystemMessage(content=_TRAINING_SYSTEM_PROMPT)] + messages
    )
    return {"messages": [response]}


def _training_condition(state: HCMState) -> Literal["training_tools", "__end__"]:
    last = state["messages"][-1]
    return "training_tools" if getattr(last, "tool_calls", None) else "__end__"


# ══════════════════════════════════════════════════════════════════
# POLICY AGENT
# ══════════════════════════════════════════════════════════════════

_POLICY_SYSTEM_PROMPT = """You are the HR Policy expert for a bank.

You answer questions about all HR policies including:
  • Leave policies (annual, sick, maternity/paternity, emergency)
  • Work from home policy
  • Code of conduct and ethics
  • Performance management and appraisals
  • Travel and expense reimbursement
  • Data privacy and information security
  • AML/KYC compliance obligations
  • Grievance redressal process

Rules:
  - Always cite the official policy name when answering
  - Provide accurate, complete answers based on policy documents
  - For compliance-related policies, emphasise the importance of adherence
  - If you need to search for a policy, use search_hr_policy with relevant keywords"""

_policy_tools    = [search_hr_policy, list_policy_categories, get_policy_by_category]
_policy_tool_node = ToolNode(_policy_tools)
_policy_llm       = _llm.bind_tools(_policy_tools)


def policy_agent_node(state: HCMState) -> dict:
    messages = sanitize_messages(state["messages"])
    response = _policy_llm.invoke(
        [SystemMessage(content=_POLICY_SYSTEM_PROMPT)] + messages
    )
    return {"messages": [response]}


def _policy_condition(state: HCMState) -> Literal["policy_tools", "__end__"]:
    last = state["messages"][-1]
    return "policy_tools" if getattr(last, "tool_calls", None) else "__end__"


# ══════════════════════════════════════════════════════════════════
# INFO AGENT
# ══════════════════════════════════════════════════════════════════

_INFO_SYSTEM_PROMPT = """You are the HR Information specialist for a bank.

You help with:
  • Looking up employee profiles (name, designation, department, email, manager)
  • Listing employees in a department
  • General HR directory queries

Rules:
  - Respect data privacy — share only appropriate, non-sensitive information
  - Do not speculate about information not in the directory"""

_info_tools    = [get_employee_info, list_employees_by_department]
_info_tool_node = ToolNode(_info_tools)
_info_llm       = _llm.bind_tools(_info_tools)


def info_agent_node(state: HCMState) -> dict:
    messages = sanitize_messages(state["messages"])
    response = _info_llm.invoke(
        [SystemMessage(content=_INFO_SYSTEM_PROMPT)] + messages
    )
    return {"messages": [response]}


def _info_condition(state: HCMState) -> Literal["info_tools", "__end__"]:
    last = state["messages"][-1]
    return "info_tools" if getattr(last, "tool_calls", None) else "__end__"


# ══════════════════════════════════════════════════════════════════
# BUILD GRAPH
# ══════════════════════════════════════════════════════════════════

def build_hcm_graph():
    builder = StateGraph(HCMState)

    # ── Nodes ──────────────────────────────────────────────────────
    builder.add_node("supervisor",      supervisor_node)

    builder.add_node("leave_agent",     leave_agent_node)
    builder.add_node("leave_tools",     _leave_tool_node)

    builder.add_node("training_agent",  training_agent_node)
    builder.add_node("training_tools",  _training_tool_node)

    builder.add_node("policy_agent",    policy_agent_node)
    builder.add_node("policy_tools",    _policy_tool_node)

    builder.add_node("info_agent",      info_agent_node)
    builder.add_node("info_tools",      _info_tool_node)

    # ── Entry ──────────────────────────────────────────────────────
    builder.add_edge(START, "supervisor")

    # ── Supervisor routing ─────────────────────────────────────────
    builder.add_conditional_edges(
        "supervisor",
        _route_from_supervisor,
        {
            "leave_agent":    "leave_agent",
            "training_agent": "training_agent",
            "policy_agent":   "policy_agent",
            "info_agent":     "info_agent",
            "END":            END,
        },
    )

    # ── Leave agent ↔ tools loop ───────────────────────────────────
    builder.add_conditional_edges(
        "leave_agent", _leave_condition,
        {"leave_tools": "leave_tools", "__end__": END},
    )
    builder.add_edge("leave_tools", "leave_agent")

    # ── Training agent ↔ tools loop ────────────────────────────────
    builder.add_conditional_edges(
        "training_agent", _training_condition,
        {"training_tools": "training_tools", "__end__": END},
    )
    builder.add_edge("training_tools", "training_agent")

    # ── Policy agent ↔ tools loop ──────────────────────────────────
    builder.add_conditional_edges(
        "policy_agent", _policy_condition,
        {"policy_tools": "policy_tools", "__end__": END},
    )
    builder.add_edge("policy_tools", "policy_agent")

    # ── Info agent ↔ tools loop ────────────────────────────────────
    builder.add_conditional_edges(
        "info_agent", _info_condition,
        {"info_tools": "info_tools", "__end__": END},
    )
    builder.add_edge("info_tools", "info_agent")

    return builder.compile()


# Module-level compiled graph — imported by main.py and streamlit_app.py
hcm_graph = build_hcm_graph()

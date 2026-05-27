"""Streamlit UI for the HCM Self-Service Assistant."""

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

from langchain_core.messages import AIMessage, HumanMessage

from hcm_agent.workflows.graph import hcm_graph

# ── Page config ────────────────────────────────────────────────────
st.set_page_config(
    page_title="HR Self-Service Assistant",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Sidebar ────────────────────────────────────────────────────────
with st.sidebar:
    st.image(
        "https://img.icons8.com/color/96/bank-building.png",
        width=60,
    )
    st.title("HR Self-Service")
    st.caption("First National Bank · HCM Assistant")
    st.divider()

    emp_id = st.text_input(
        "🪪 Your Employee ID",
        value="EMP001",
        placeholder="e.g. EMP001",
        help="Enter your employee ID to personalise responses",
    )

    st.divider()

    # ── Quick actions ──────────────────────────────────────────────
    st.markdown("**⚡ Quick Actions**")

    quick_groups = {
        "📅 Leave": [
            "Check my leave balance",
            "Show my leave history",
            "Apply for annual leave next week",
        ],
        "🎓 Training": [
            "Show available training sessions",
            "List mandatory compliance courses",
            "What training am I enrolled in?",
        ],
        "📋 Policy": [
            "What is the annual leave policy?",
            "Explain the work from home policy",
            "What are the AML/KYC obligations?",
        ],
        "👤 Info": [
            "Show my employee profile",
            "Who is in the Compliance team?",
        ],
    }

    for group, actions in quick_groups.items():
        with st.expander(group, expanded=False):
            for action in actions:
                if st.button(action, key=action, use_container_width=True):
                    st.session_state["quick_action"] = action

    st.divider()

    # ── Agent legend ───────────────────────────────────────────────
    st.markdown("**🤖 Active Agents**")
    st.markdown(
        """
        | Agent | Handles |
        |---|---|
        | 📅 Leave | Balance, requests, history |
        | 🎓 Training | Enrol, cancel, browse |
        | 📋 Policy | HR guidelines, rules |
        | 👤 Info | Directory, profiles |
        """
    )

    st.divider()
    if st.button("🗑️ Clear Conversation", use_container_width=True):
        st.session_state["messages"]     = []
        st.session_state["quick_action"] = None
        st.rerun()

# ── Session state init ─────────────────────────────────────────────
if "messages"     not in st.session_state:
    st.session_state["messages"] = []
if "quick_action" not in st.session_state:
    st.session_state["quick_action"] = None

# ── Main area ──────────────────────────────────────────────────────
col_title, col_badge = st.columns([4, 1])
with col_title:
    st.title("🏦 HR Self-Service Assistant")
    st.markdown(
        f"Welcome, **{emp_id}** — Ask me about leave, training, policies, or your employee profile."
    )
with col_badge:
    st.markdown("<br>", unsafe_allow_html=True)
    st.success("🟢 Online")

st.divider()

# ── Render chat history ────────────────────────────────────────────
for msg in st.session_state["messages"]:
    if isinstance(msg, HumanMessage):
        # Strip the injected employee context prefix before displaying
        display_text = msg.content
        prefix = f"[Employee ID: {emp_id}] "
        if display_text.startswith(prefix):
            display_text = display_text[len(prefix):]
        with st.chat_message("user"):
            st.markdown(display_text)
    elif isinstance(msg, AIMessage) and msg.content:
        with st.chat_message("assistant", avatar="🤖"):
            st.markdown(msg.content)

# ── Handle input ───────────────────────────────────────────────────
# st.chat_input() MUST be called on every render so the bar stays visible.
# We then decide whether to use a quick-action value or the typed value.
chat_input = st.chat_input(
    "Ask about leave, training courses, HR policies, or employee info…"
)

if st.session_state["quick_action"]:
    prompt = st.session_state["quick_action"]
    st.session_state["quick_action"] = None
elif chat_input:
    prompt = chat_input
else:
    prompt = None

if prompt:
    full_prompt = f"[Employee ID: {emp_id}] {prompt}"
    human_msg   = HumanMessage(content=full_prompt)

    # Show user bubble immediately
    with st.chat_message("user"):
        st.markdown(prompt)

    st.session_state["messages"].append(human_msg)

    # ── Call the graph ─────────────────────────────────────────────
    with st.chat_message("assistant", avatar="🤖"):
        with st.spinner("Thinking…"):
            try:
                result = hcm_graph.invoke({"messages": st.session_state["messages"]})

                # Extract the last AI message with content
                response_text = ""
                new_messages  = result["messages"][len(st.session_state["messages"]):]
                for msg in reversed(new_messages):
                    if isinstance(msg, AIMessage) and msg.content:
                        response_text = msg.content
                        break

                if not response_text:
                    response_text = "I've processed your request. Is there anything else I can help you with?"

                st.markdown(response_text)

                # ── Routing metadata badge ─────────────────────────
                agent  = result.get("next_agent", "")
                intent = result.get("intent", "")
                agent_icons = {
                    "leave_agent":    "📅 Leave Agent",
                    "training_agent": "🎓 Training Agent",
                    "policy_agent":   "📋 Policy Agent",
                    "info_agent":     "👤 Info Agent",
                }
                if agent and agent in agent_icons:
                    st.caption(
                        f"🔀 Routed to **{agent_icons[agent]}** · intent: `{intent}`"
                    )

                # Update session state with full result
                st.session_state["messages"] = result["messages"]

            except Exception as exc:
                st.error(f"⚠️ An error occurred: {exc}")
                st.info("Please check your `.env` file and ensure `OPENAI_API_KEY` is set.")

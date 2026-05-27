"""CLI entry point for the HCM Self-Service Assistant."""

from dotenv import load_dotenv

load_dotenv()

from langchain_core.messages import AIMessage, HumanMessage

from hcm_agent.workflows.graph import hcm_graph

_BANNER = """
╔══════════════════════════════════════════════════════╗
║   🏦  First National Bank — HR Self-Service          ║
║   AI-powered HCM Assistant  |  Powered by LangGraph  ║
╚══════════════════════════════════════════════════════╝

  You can ask me about:
    • Leave balance & requests       (e.g. "I want 3 days annual leave")
    • Training & enrollments         (e.g. "Show me compliance courses")
    • HR policies & guidelines       (e.g. "What is the WFH policy?")
    • Employee information           (e.g. "Who is in the Compliance team?")

  Type  'exit'  or  'quit'  to end the session.
"""


def main() -> None:
    print(_BANNER)
    emp_id = input("Enter your Employee ID (default: EMP001): ").strip() or "EMP001"
    print(f"\n✅  Logged in as: {emp_id}\n{'─' * 54}\n")

    messages: list = []

    while True:
        try:
            user_input = input("You: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n\nSession ended. Have a great day!")
            break

        if not user_input:
            continue

        if user_input.lower() in ("exit", "quit", "bye"):
            print("\nThank you for using HR Self-Service. Have a great day!")
            break

        # Inject employee context so every agent knows who is asking
        full_prompt = f"[Employee ID: {emp_id}] {user_input}"
        messages.append(HumanMessage(content=full_prompt))

        try:
            result   = hcm_graph.invoke({"messages": messages})
            messages = result["messages"]

            # Show which agent handled it
            agent  = result.get("next_agent", "")
            intent = result.get("intent", "")
            if agent and agent != "END":
                print(f"\n  ℹ️  Routed to: {agent}  |  intent: {intent}")

            # Print the last AI message with content
            for msg in reversed(messages):
                if isinstance(msg, AIMessage) and msg.content:
                    print(f"\nAssistant: {msg.content}\n{'─' * 54}\n")
                    break

        except Exception as exc:
            print(f"\n⚠️  Error: {exc}\n")


if __name__ == "__main__":
    main()

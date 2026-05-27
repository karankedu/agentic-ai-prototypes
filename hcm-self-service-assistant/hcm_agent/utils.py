from langchain_core.messages import BaseMessage


def sanitize_messages(messages: list[BaseMessage]) -> list[BaseMessage]:
    """Replace empty / None message content with a single space.

    Some LLM APIs (including certain OpenAI-compatible endpoints) reject
    messages whose content is an empty string or None. This guard is a
    defensive measure applied before every LLM invocation.
    """
    sanitized: list[BaseMessage] = []
    for msg in messages:
        if not msg.content:
            msg = msg.model_copy(update={"content": " "})
        sanitized.append(msg)
    return sanitized

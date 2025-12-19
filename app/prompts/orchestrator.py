def build_chat_prompt(
    message: str,
    image_context: str | None = None
) -> str:
    parts = []

    parts.append(
        """
You are a helpful AI health assistant.

Rules:
- Do NOT provide medical diagnosis
- Do NOT replace healthcare professionals
- Give educational and practical insights only
- Use clear, friendly language
"""
    )

    if image_context:
        parts.append(
            f"""
Image analysis context:
{image_context}
"""
        )

    parts.append(
        f"""
User question:
{message}
"""
    )

    parts.append(
        """
Respond with:
- Clear explanation
- Health insight if relevant
- Safety reminder when necessary
"""
    )

    return "\n".join(parts).strip()

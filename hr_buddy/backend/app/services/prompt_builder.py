"""Build the grounded prompt sent to the LLM."""
from ..services.retriever import RetrievedChunk

SYSTEM_PROMPT = """You are HR Buddy, the internal HR and policy assistant for SkillSync HRMS.

YOUR ROLE
- Answer employee questions using ONLY the retrieved company policy context provided below.
- Be accurate, calm, clear, and professional at all times.
- Never invent, assume, or extrapolate policy details not explicitly present in the context.

ANSWER FORMAT (always follow this order)
1. Direct answer — one sentence, clear and immediate.
2. Short explanation — 2-4 sentences maximum, citing relevant policy details.
3. Source — "Source: Page X" (list multiple pages if relevant).

SPECIAL RULES
- If the answer is in the policy: give the direct answer first, then explain, then cite.
- If the answer is partially in the policy: state clearly what IS known and note what is NOT covered.
- If the answer is NOT in the policy at all: say exactly "I could not find this in the current HR policy document." Do not guess.
- For leave, attendance, resignation, termination, skill progression, learning resources, hierarchy, or remote work questions: prioritize exact policy wording and page citations.
- If a question is ambiguous: ask one short clarifying question before answering.
- Never provide legal advice beyond what is written in the document.
- Format answers for employees, not for developers or HR specialists.
- Keep answers concise — employees want quick, clear guidance.

TONE
Professional, warm, helpful. Use plain language. Avoid jargon unless it appears in the policy itself."""


def build_prompt(query: str, chunks: list[RetrievedChunk]) -> tuple[str, str]:
    """
    Returns (system_message, user_message) ready for chat completion.
    """
    if not chunks:
        context_block = "No relevant policy sections were found for this query."
    else:
        context_parts = []
        for i, c in enumerate(chunks, start=1):
            context_parts.append(f"[Context {i} — Page {c.page}]\n{c.text}")
        context_block = "\n\n---\n\n".join(context_parts)

    user_message = f"""Retrieved policy context:

{context_block}

---

Employee question: {query}

Please answer using ONLY the context above. Follow the answer format exactly."""

    return SYSTEM_PROMPT, user_message


def build_fallback_answer(query: str, chunks: list[RetrievedChunk]) -> str:
    """
    Used when no LLM is configured. Summarises retrieved chunks directly.
    """
    if not chunks:
        return "I could not find this in the current HR policy document."

    best = chunks[0]
    lines = [
        f"Based on the HR policy (Page {best.page}):",
        "",
        best.text[:600].rstrip() + ("…" if len(best.text) > 600 else ""),
    ]
    if len(chunks) > 1:
        extra_pages = sorted({c.page for c in chunks[1:]})
        lines.append(f"\nAdditional related sections on page(s): {', '.join(map(str, extra_pages))}")
    return "\n".join(lines)

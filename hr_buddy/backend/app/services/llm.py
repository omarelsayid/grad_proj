"""LLM client — OpenAI-compatible, configurable BASE_URL + API_KEY."""
import logging
from typing import Optional

logger = logging.getLogger("hr_buddy.llm")


def chat_complete(
    system: str,
    user: str,
    base_url: str,
    api_key: str,
    model: str,
    temperature: float = 0.2,
    max_tokens: int = 1024,
) -> Optional[str]:
    """
    Call an OpenAI-compatible chat completions endpoint.
    Returns the assistant message text, or None on failure.
    """
    if not base_url or not api_key:
        logger.warning("LLM not configured (LLM_BASE_URL / LLM_API_KEY missing) — using fallback")
        return None

    try:
        from openai import OpenAI

        client = OpenAI(base_url=base_url, api_key=api_key)
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content
    except ImportError:
        logger.error("openai package not installed — run: pip install openai")
        return None
    except Exception as exc:
        logger.error("LLM call failed: %s", exc)
        return None

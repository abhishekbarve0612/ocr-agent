from __future__ import annotations
from typing import Tuple, Dict, Any
from django.conf import settings
from openai import OpenAI

from .prompts import SYSTEM_PROMPT

_MD_SUFFIX = (
    "You are a formatting engine.\n"
    "Always return GitHub-Flavored Markdown (GFM) as final output."
)

_client: OpenAI | None = None

def client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=getattr(settings, "OPENAI_API_KEY", None))
    return _client

def chat_markdown(instruction: str, context: str, *, model: str, temperature: float, max_tokens: int) -> tuple[str, dict]:
    system_prompt = SYSTEM_PROMPT
    user_prompt = f"<ocr>\n{context}\n</ocr>\n<task>\n{instruction}\n</task>"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    response = client().chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format={"type": "text"},
    )

    content = response.choices[0].message.content or ""
    usage = {
        "prompt_tokens": getattr(response.usage, "prompt_tokens", None),
        "completion_tokens": getattr(response.usage, "completion_tokens", None),
        "total_tokens": getattr(response.usage, "total_tokens", None),
        "id": getattr(response, "id", None),
    }
    return content, usage

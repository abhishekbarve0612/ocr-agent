from __future__ import annotations
from typing import Tuple, Dict, Any
from django.conf import settings
from openai import OpenAI

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

def chat_markdown(instruction: str, prompt: str, *, model: str, temperature: float, max_tokens: int) -> tuple[str, dict]:
    system_prompt = (instruction or "").strip()
    if "markdown" not in system_prompt.lower():
        system_prompt = f"{system_prompt}\n\n{_MD_SUFFIX}".strip()

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": prompt},
    ]

    resp = client().chat.completions.create(
        model=model,
        messages=messages,
        temperature=temperature,
        max_tokens=max_tokens,
        response_format={"type": "text"},
    )

    content = resp.choices[0].message.content or ""
    usage = {
        "prompt_tokens": getattr(resp.usage, "prompt_tokens", None),
        "completion_tokens": getattr(resp.usage, "completion_tokens", None),
        "total_tokens": getattr(resp.usage, "total_tokens", None),
        "id": getattr(resp, "id", None),
    }
    return content, usage

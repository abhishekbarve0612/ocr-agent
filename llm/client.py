from __future__ import annotations
from collections.abc import Callable
from typing import Optional
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

def chat_markdown(
    instruction: str,
    context: str,
    *,
    model: str,
    temperature: float,
    max_tokens: int,
    on_token: Optional[Callable[[str], None]] = None,
) -> tuple[str, dict]:
    system_prompt = SYSTEM_PROMPT
    user_prompt = f"<ocr>\n{context}\n</ocr>\n<task>\n{instruction}\n</task>"

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

    # REF: https://til.simonwillison.net/gpt3/python-chatgpt-streaming-api
    if on_token:
        stream = client().chat.completions.create(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format={"type": "text"},
            stream=True,
        )
        parts: list[str] = []
        usage: dict = {
            "prompt_tokens": None,
            "completion_tokens": None,
            "total_tokens": None,
            "id": None,
        }
        for chunk in stream:
            choice = chunk.choices[0] if chunk.choices else None
            delta = getattr(choice, "delta", None)
            content = getattr(delta, "content", None)
            if content:
                parts.append(content)
                on_token(content)
            chunk_usage = getattr(chunk, "usage", None)
            if chunk_usage:
                usage = {
                    "prompt_tokens": getattr(chunk_usage, "prompt_tokens", None),
                    "completion_tokens": getattr(chunk_usage, "completion_tokens", None),
                    "total_tokens": getattr(chunk_usage, "total_tokens", None),
                    "id": getattr(chunk, "id", None),
                }
        return "".join(parts), usage

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

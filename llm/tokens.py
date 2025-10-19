from __future__ import annotations
import hashlib, json
from typing import List, Dict
import tiktoken

def strong_hash(obj: dict) -> str:
    b = json.dumps(obj, sort_keys=True, ensure_ascii=False).encode("utf-8")
    return hashlib.sha256(b).hexdigest()

def _encoding_for(model: str):
    try:
        return tiktoken.encoding_for_model(model)
    except Exception:
        return tiktoken.get_encoding("cl100k_base")

def count_tokens_text(text: str, model: str) -> int:
    enc = _encoding_for(model)
    return len(enc.encode(text or ""))

def count_tokens_messages(messages: List[Dict[str, str]], model: str) -> int:
    return sum(count_tokens_text(m.get("content",""), model) + 3 for m in messages)

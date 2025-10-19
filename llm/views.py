from __future__ import annotations
import json
from django.conf import settings
from django.http import JsonResponse, HttpRequest
from django.views.decorators.csrf import csrf_exempt

from .models import LLMRequest
from .tokens import strong_hash, count_tokens_messages
from .client import chat_markdown

def _defaults():
    return (
        getattr(settings, "LLM_DEFAULT_MODEL", "gpt-4o-mini"),
        float(getattr(settings, "LLM_DEFAULT_TEMPERATURE", 0.2)),
        int(getattr(settings, "LLM_DEFAULT_MAX_TOKENS", 800)),
    )

@csrf_exempt
def generate(request: HttpRequest):
    if request.method != "POST":
        return JsonResponse({"detail": "POST only"}, status=405)

    try:
        data = json.loads(request.body.decode("utf-8"))
    except Exception:
        return JsonResponse({"detail": "Invalid JSON"}, status=400)

    instruction = (data.get("instruction") or "").strip()
    prompt = (data.get("prompt") or "").strip()
    if not instruction or not prompt:
        return JsonResponse({"detail": "instruction and prompt are required"}, status=400)

    default_model, default_temperature, default_max_tokens = _defaults()
    model = (data.get("model") or default_model).strip() 
    temperature = float(data.get("temperature") if data.get("temperature") is not None else default_temperature)
    max_tokens = int(data.get("max_tokens") if data.get("max_tokens") is not None else default_max_tokens)
    use_cache = bool(data.get("use_cache", True))

    request_payload = {
        "instruction": instruction,
        "prompt": prompt,
        "model": model,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "_v": 1,
    }
    request_hash = strong_hash(request_payload)

    if use_cache:
        existing = LLMRequest.objects.filter(request_hash=request_hash, response_md__isnull=False).first()
        if existing:
            existing.cached_hit = True
            existing.save(update_fields=["cached_hit", "updated_at"])
            return JsonResponse({
                "id": str(existing.id),
                "cached": True,
                "model": existing.model,
                "response_md": existing.response_md,
                "usage": {
                    "input_tokens_est": existing.input_tokens_est,
                    "input_tokens": existing.input_tokens,
                    "output_tokens": existing.output_tokens,
                },
                "status": "COMPLETED",
            })

    messages = [
        {"role": "system", "content": instruction},
        {"role": "user", "content": prompt},
    ]
    input_tokens_est = count_tokens_messages(messages, model)

    job = LLMRequest.objects.create(
        instruction=instruction,
        prompt=prompt,
        model=model,
        temperature=temperature,
        max_tokens=max_tokens,
        request_hash=request_hash,
        input_tokens_est=input_tokens_est,
    )

    try:
        content, usage = chat_markdown(
            instruction, prompt,
            model=model, temperature=temperature, max_tokens=max_tokens
        )
        job.response_md = content
        job.input_tokens = usage.get("prompt_tokens")
        job.output_tokens = usage.get("completion_tokens")
        job.save(update_fields=["response_md", "input_tokens", "output_tokens", "updated_at"])

        return JsonResponse({
            "id": str(job.id),
            "cached": False,
            "model": job.model,
            "response_md": job.response_md,
            "usage": {
                "input_tokens_est": job.input_tokens_est,
                "input_tokens": job.input_tokens,
                "output_tokens": job.output_tokens,
            },
            "status": "COMPLETED",
        })
    except Exception as e:
        job.error = str(e)
        job.save(update_fields=["error", "updated_at"])
        return JsonResponse({"id": str(job.id), "status": "ERROR", "error": job.error}, status=500)

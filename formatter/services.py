from collections.abc import Iterable
from dotenv import load_dotenv
import os
import threading

from django.conf import settings
from django.contrib.auth.models import User
from django.db import close_old_connections

from llm.client import chat_markdown
from llm.tokens import count_tokens_text
from ocr.models import OCRDocument

from .models import FormatterRun, FormatterChunk

load_dotenv()

MAX_OUTPUT_TOKENS = settings.MAX_OUTPUT_TOKENS or int(os.getenv("MAX_OUTPUT_TOKENS", "16384"))
MAX_INPUT_TOKENS = settings.MAX_INPUT_TOKENS or int(os.getenv("MAX_INPUT_TOKENS", "16000"))


def _format_page_label(page_numbers: Iterable[int]) -> str:
    numbers = list(page_numbers)
    if not numbers:
        return ""
    if len(numbers) == 1:
        return str(numbers[0])
    return f"{numbers[0]}-{numbers[-1]}"


def run_formatter_job(ocr_document: OCRDocument, prompt: str, user: User):
    formatter_run = FormatterRun.objects.create(
        ocr_document=ocr_document,
        prompt=prompt,
        user=user,
    )

    def worker(run_id: int):
        close_old_connections()
        formatter_run = FormatterRun.objects.select_related("ocr_document").get(id=run_id)
        formatter_run.status = FormatterRun.Status.RUNNING
        formatter_run.error = ""
        formatter_run.save(update_fields=["status", "error"])

        pages = list(formatter_run.ocr_document.pages.order_by("page_number"))

        def invoke_formatter(context_text: str, page_numbers: list[int]) -> dict:
            chunk = FormatterChunk.objects.create(
                run=formatter_run,
                pages=_format_page_label(page_numbers),
                input_chars=len(context_text),
                input_tokens=0,
                output_tokens=0,
                output_markdown="",
            )

            def on_token(delta: str):
                chunk.output_markdown = (chunk.output_markdown or "") + delta
                chunk.save(update_fields=["output_markdown"])

            response_text, usage = chat_markdown(
                instruction=formatter_run.prompt,
                context=context_text,
                model=settings.LLM_MODEL,
                temperature=0.2,
                max_tokens=MAX_OUTPUT_TOKENS,
                on_token=on_token,
            )
            chunk.output_markdown = response_text
            chunk.input_tokens = (usage or {}).get("prompt_tokens") or 0
            chunk.output_tokens = (usage or {}).get("completion_tokens") or 0
            chunk.save(update_fields=["output_markdown", "input_tokens", "output_tokens"])
            return usage

        if not pages:
            formatter_run.status = FormatterRun.Status.FAILED
            formatter_run.error = "No OCR pages available for formatting."
            formatter_run.save(update_fields=["status", "error"])
            return

        complete_text = "\n\n".join((page.text or "") for page in pages)
        total_input_tokens = 0
        total_output_tokens = 0

        try:
            token_count = count_tokens_text(complete_text, settings.LLM_MODEL)
            if token_count > MAX_INPUT_TOKENS:
                context_fragments: list[str] = []
                context_page_numbers: list[int] = []
                context_tokens = 0

                for page in pages:
                    page_text = page.text or ""
                    page_tokens = count_tokens_text(page_text, settings.LLM_MODEL)

                    if context_fragments and context_tokens + page_tokens > MAX_INPUT_TOKENS:
                        context_text = "".join(context_fragments)
                        usage = invoke_formatter(context_text, context_page_numbers)
                        total_input_tokens += (usage or {}).get("prompt_tokens") or 0
                        total_output_tokens += (usage or {}).get("completion_tokens") or 0
                        context_fragments = []
                        context_page_numbers = []
                        context_tokens = 0

                    context_fragments.append(f"Page {page.page_number}: {page_text}\n\n")
                    context_page_numbers.append(page.page_number)
                    context_tokens += page_tokens

                if context_fragments:
                    context_text = "".join(context_fragments)
                    usage = invoke_formatter(context_text, context_page_numbers)
                    total_input_tokens += (usage or {}).get("prompt_tokens") or 0
                    total_output_tokens += (usage or {}).get("completion_tokens") or 0
            else:
                usage = invoke_formatter(
                    complete_text,
                    [page.page_number for page in pages],
                )
                total_input_tokens += (usage or {}).get("prompt_tokens") or 0
                total_output_tokens += (usage or {}).get("completion_tokens") or 0

            formatter_run.status = FormatterRun.Status.COMPLETED
        except Exception as exc:
            formatter_run.status = FormatterRun.Status.FAILED
            formatter_run.error = str(exc)
        finally:
            formatter_run.total_input_tokens = total_input_tokens
            formatter_run.total_output_tokens = total_output_tokens
            update_fields = ["status", "total_input_tokens", "total_output_tokens"]
            if formatter_run.error:
                update_fields.append("error")
            formatter_run.save(update_fields=update_fields)

    threading.Thread(target=worker, args=(formatter_run.id,), daemon=True).start()
    return formatter_run

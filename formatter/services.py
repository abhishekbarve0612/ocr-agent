import token
from django.conf import settings
from llm.client import chat_markdown
from llm.tokens import count_tokens_text, count_tokens_messages
from ocr.models import OCRDocument
from django.contrib.auth.models import User
from .models import FormatterRun, FormatterChunk

MAX_TOKENS = 16000
MAX_CHARS = 60000

def run_formatter_job(ocr_document: OCRDocument, prompt: str, user: User):
    document_pages = ocr_document.pages.all()
    
    formatter_run = FormatterRun.objects.create(
        ocr_document=ocr_document,
        prompt=prompt,
        user=user,
    )
    complete_text = '\n\n'.join(page.text for page in document_pages)
    token_count = count_tokens_text(complete_text, settings.LLM_MODEL) if document_pages else 0
    if token_count > MAX_TOKENS:
        context = ''
        page_count = 0
        token_count = 0
        start_page = 1
        for page_number, page in enumerate(document_pages, start=1):
            page_text = page.text
            token_count += count_tokens_text(page_text, settings.LLM_MODEL)
            if token_count < MAX_TOKENS:
                context += f"Page {page_number}: {page_text}\n\n"
                page_count += 1
            else:
                response_text, usage = chat_markdown(prompt, context, model=settings.LLM_MODEL, temperature=0.2, max_tokens=MAX_TOKENS)
                chunk = FormatterChunk.objects.create(
                    run=formatter_run,
                    pages=f"{start_page}-{page_number - 1}",
                    input_chars=len(context),
                    input_tokens=usage['prompt_tokens'],
                    output_tokens=usage['completion_tokens'],
                    output_markdown=response_text,
                )
                start_page = page_number
                context = ''
                token_count = 0
                page_count = 0
        if context:
            response_text, usage = chat_markdown(prompt, context, model=settings.LLM_MODEL, temperature=0.2, max_tokens=MAX_TOKENS)
            chunk = FormatterChunk.objects.create(
                run=formatter_run,
                pages=f"{start_page}-{document_pages.count()}",
                input_chars=len(context),
                input_tokens=usage['prompt_tokens'],
                output_tokens=usage['completion_tokens'],
                output_markdown=response_text,
            )
    else:
        response_text, usage = chat_markdown(prompt, complete_text, model=settings.LLM_MODEL, temperature=0.2, max_tokens=MAX_TOKENS)
        chunk = FormatterChunk.objects.create(
            run=formatter_run,
            pages=f"1-{document_pages.count()}",
            input_chars=len(complete_text),
            input_tokens=usage['prompt_tokens'],
            output_tokens=usage['completion_tokens'],
            output_markdown=response_text,
        )
    formatter_run.status = FormatterRun.Status.COMPLETED
    formatter_run.total_input_tokens = usage['prompt_tokens']
    formatter_run.total_output_tokens = usage['completion_tokens']
    formatter_run.save(update_fields=['status', 'total_input_tokens', 'total_output_tokens'])
    return formatter_run
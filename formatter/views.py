from pathlib import Path

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.utils.text import slugify

from ocr.models import OCRDocument

from .forms import FormatterForm
from .models import FormatterRun
from .services import run_formatter_job


@login_required
def formatter_form(request, document_id: int):
    document = get_object_or_404(OCRDocument, id=document_id)
    if request.method == 'POST':
        form = FormatterForm(request.POST, document=document)
        if form.is_valid():
            run = run_formatter_job(
                ocr_document=form.cleaned_data['document'],
                prompt=form.cleaned_data['prompt'],
                user=request.user,
            )
            return redirect('formatter:run_detail', run_id=run.id)
    else:
        form = FormatterForm(document=document)

    return render(request, 'formatter/start.html', {'form': form, 'document': document})


def _load_markdown_output(run: FormatterRun) -> str:
    if run.output_markdown:
        try:
            with run.output_markdown.open('r') as stream:
                data = stream.read()
            if data.strip():
                return data
        except (FileNotFoundError, OSError):
            pass

    parts = [chunk.output_markdown.strip() for chunk in run.chunks.order_by('id') if chunk.output_markdown]
    return '\n\n'.join(part for part in parts if part)


@login_required
def formatter_run_detail(request, run_id: int):
    run = get_object_or_404(FormatterRun, id=run_id)
    content = _load_markdown_output(run)
    if request.GET.get("format") == "json" or request.headers.get("Accept") == "application/json":
        return JsonResponse(
            {
                "run_id": run.id,
                "status": run.status,
                "status_display": run.get_status_display(),
                "error": run.error,
                "markdown_content": content,
            }
        )
    return render(
        request,
        'formatter/run_detail.html',
        {
            'run': run,
            'markdown_content': content,
        },
    )


@login_required
def formatter_run_download(request, run_id: int):
    run = get_object_or_404(FormatterRun, id=run_id)
    content = _load_markdown_output(run)
    if not content:
        return HttpResponse('No formatter output is available yet for this run.', status=404)

    original_name = Path(run.ocr_document.document.file.name).stem or f'document-{run.ocr_document.id}'
    filename = f"{slugify(original_name) or 'formatted'}-run-{run.id}.md"

    response = HttpResponse(content, content_type='text/markdown; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

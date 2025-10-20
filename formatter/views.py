from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect

from ocr.models import OCRDocument

from .forms import FormatterForm
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
            return redirect('ocr:document_detail', file_id=run.ocr_document.id)
    else:
        form = FormatterForm(document=document)

    return render(request, 'formatter/start.html', {'form': form, 'document': document})

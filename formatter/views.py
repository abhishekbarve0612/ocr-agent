from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.conf import settings

from ocr.models import OCRDocument

from .forms import FormatterForm
from .models import FormatterRun
from .services import run_formatter_job


@login_required
def formatter_form(request, document_id: int):
    document = get_object_or_404(OCRDocument, id=document_id)
    form = FormatterForm(request.POST or None, initial={'document': document})
    
    if request.method == 'POST' and form.is_valid():
        run = run_formatter_job(
            ocr_document=document,
            prompt=form.cleaned_data['prompt'],
            user=request.user,
        )
        return redirect(reverse('formatter:run_detail', kwargs={'run_id': run.id}))
    
    return render(request, 'formatter/start.html', {'form': form, 'document': document})
from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

from formatter.models import FormatterRun
from .forms import UploadFileForm
from .models import UploadedFile

def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('uploads:file')
    else:
        form = UploadFileForm()
    files = (
        UploadedFile.objects
        .prefetch_related('ocr_documents__formatter_runs__chunks')
        .order_by('-created_at')
    )

    for file_obj in files:
        latest_run = None
        for document in file_obj.ocr_documents.all():
            for run in sorted(document.formatter_runs.all(), key=lambda r: r.created_at, reverse=True):
                if run.status != FormatterRun.Status.COMPLETED:
                    continue
                has_file = bool(run.output_markdown)
                has_chunks = any((chunk.output_markdown or '').strip() for chunk in run.chunks.all())
                if has_file or has_chunks:
                    latest_run = run
                    break
            if latest_run:
                break
        file_obj.latest_formatter_run = latest_run

    return render(request, 'uploads/upload.html', {'form': form, 'files': files})

def delete_file(request, file_id: int):
    file = get_object_or_404(UploadedFile, id=file_id)
    file.delete()
    messages.add_message(request, messages.SUCCESS, 'File deleted successfully')
    return redirect('uploads:file')

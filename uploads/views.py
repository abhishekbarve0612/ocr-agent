from django.contrib import messages
from django.shortcuts import render, redirect, get_object_or_404

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
    files = UploadedFile.objects.all().order_by('-created_at')
    return render(request, 'uploads/upload.html', {'form': form, 'files': files})

def delete_file(request, file_id: int):
    file = get_object_or_404(UploadedFile, id=file_id)
    file.delete()
    messages.add_message(request, messages.SUCCESS, 'File deleted successfully')
    return redirect('uploads:file')
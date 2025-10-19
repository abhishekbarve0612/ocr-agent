from django.shortcuts import render, redirect

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
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone

from uploads.models import UploadedFile
from .models import OCRDocument, OCRPage
from .forms import OCRStartForm
from .services import get_ocr_doc_results, azure_read_text, parse_page_range

def start_ocr(request, file_id: int):
    file_obj = get_object_or_404(UploadedFile, id=file_id)
    
    if request.method == 'POST':
        form = OCRStartForm(request.POST)
        if form.is_valid():
            page_range = form.cleaned_data['page_range'] or 'all'
            languages = form.cleaned_data['languages'] or 'eng'
            
            document = OCRDocument.objects.filter(document=file_obj).order_by('-created_at').first()
            if document:
                print(f"Document: {document.id}")
                from django.urls import reverse
                return redirect(f"{reverse('ocr:document_detail', kwargs={'file_id': document.id})}?page_range={page_range}")
            else:
                document = OCRDocument.objects.create(
                    document = file_obj,
                    page_range = page_range,
                    languages = languages,
                    status = OCRDocument.Status.PENDING,
                )
                document.status = OCRDocument.Status.PROCESSING
                document.started_at = timezone.now()
                document.save(update_fields=['status', 'started_at'])
                
                try:
                    for result in azure_read_text(file_obj.file.path, page_range):
                        print(f"Result: {result}")
                        OCRPage.objects.update_or_create(
                            document=document,
                            page_number=result.page_number,
                            defaults={
                                'source': result.source,
                                'text': result.text,
                                'average_confidence': result.average_confidence,
                            }
                        )
                    document.status = OCRDocument.Status.COMPLETED
                except Exception as e:
                    document.status = OCRDocument.Status.FAILED
                    document.error_message = str(e)
                finally:
                    document.completed_at = timezone.now()
                    document.save(update_fields=['status', 'error_message', 'completed_at'])
                from django.urls import reverse
                return redirect(f"{reverse('ocr:document_detail', kwargs={'file_id': document.id})}?page_range={page_range}")
    else:
        form = OCRStartForm()
        
    return render(
        request,
        'ocr/start.html',
        {
            'form': form,
            'file_obj': file_obj,
        }
    )
    
def document_detail(request, file_id: int):
    page_range = request.GET.get('page_range')
    print(f"Document detail for file -------------------------------------------- {file_id} page_range={page_range}")
    document = get_object_or_404(OCRDocument, id=file_id)
    if page_range:
        # parse user-supplied page_range like "1-2"
        # Assume document.document.file.size or (better) document.pages.count()
        total_pages = document.pages.count()
        pages_list = parse_page_range(page_range, total_pages)
        pages = document.pages.filter(page_number__in=pages_list)
    else:
        pages = document.pages.all()
    full_text = '\n\n'.join(page.text for page in pages)
    return render(
        request,
        'ocr/document_detail.html',
        {
            'document': document,
            'pages': pages,
            'full_text': full_text,
        }
    )
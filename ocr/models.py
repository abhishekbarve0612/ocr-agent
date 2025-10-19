from django.db import models

class OCRDocument(models.Model):
    class Status(models.TextChoices):
        PENDING = 'pending'
        PROCESSING = 'processing'
        COMPLETED = 'completed'
        FAILED = 'failed'
        
    class Language(models.TextChoices):
        ENGLISH = 'eng'
        HINDI = 'hin'
        ENGLISH_HINDI = 'hin+eng'
        
    document = models.ForeignKey(
        'uploads.UploadedFile',
        on_delete=models.CASCADE,
        related_name='ocr_documents',
    )
    page_range = models.CharField(max_length=100, blank=True, help_text="e.g. 'all', '1-10', '1,3,5-7', '1-3,5'")
    languages = models.CharField(max_length=10, choices=Language.choices, blank=True)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"OCR Document {self.id} on {self.document.file.name}"

class OCRPage(models.Model):
    class Source(models.TextChoices):
        PDF_TEXT = 'pdf_text'
        OCR = 'ocr'
        
    document = models.ForeignKey(
        OCRDocument,
        on_delete=models.CASCADE,
        related_name='pages',
    )
    page_number = models.PositiveIntegerField()
    source = models.CharField(max_length=10, choices=Source.choices)
    text = models.TextField()
    average_confidence = models.FloatField(null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('document', 'page_number')
        ordering = ['page_number']
        
    def __str__(self):
        return f"Document {self.document.id} - Page {self.page_number} - {self.source}"
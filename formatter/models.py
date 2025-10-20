from django.conf import settings
from django.db import models
from django.contrib.auth.models import User

from ocr.models import OCRDocument

class FormatterRun(models.Model):
    class Status(models.TextChoices):
        IN_QUEUE = 'in_queue'
        RUNNING = 'running'
        COMPLETED = 'completed'
        FAILED = 'failed'
    
    ocr_document = models.ForeignKey(OCRDocument, on_delete=models.CASCADE, related_name='formatter_runs')
    prompt = models.TextField()
    model = models.CharField(max_length=255, default=settings.LLM_MODEL)
    status = models.CharField(max_length=255, choices=Status.choices, default=Status.IN_QUEUE)
    error = models.TextField(null=True, blank=True)
    total_input_tokens = models.IntegerField(default=0)
    total_output_tokens = models.IntegerField(default=0)
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='formatter_runs')
    
    output_markdown = models.FileField(upload_to='formatter/output_markdown/', null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Formatter Run {self.id} for {self.ocr_document.document.file.name}"
    
class FormatterChunk(models.Model):
    run = models.ForeignKey(FormatterRun, on_delete=models.CASCADE, related_name='chunks')
    pages = models.CharField(max_length=255, help_text="e.g. '1-3,5'")
    input_chars = models.IntegerField(default=0)
    output_markdown = models.TextField(blank = True)
    input_tokens = models.IntegerField(default=0)
    output_tokens = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Formatter Chunk {self.id} for {self.run.ocr_document.document.file.name}"
from __future__ import annotations
import uuid
from django.db import models

class LLMRequest(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    instruction = models.TextField()
    prompt = models.TextField()
    model = models.CharField(max_length=64, default="gpt-4o-mini")
    temperature = models.FloatField(default=0.2)
    max_tokens = models.IntegerField(default=800)
    request_hash = models.CharField(max_length=64, unique=True, db_index=True)
    response_md = models.TextField(null=True, blank=True)
    input_tokens_est = models.IntegerField(default=0)
    input_tokens = models.IntegerField(null=True, blank=True)
    output_tokens = models.IntegerField(null=True, blank=True)

    error = models.TextField(null=True, blank=True)
    cached_hit = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.id} cached={self.cached_hit}"

from django.contrib import admin
from .models import LLMRequest

@admin.register(LLMRequest)
class LLMRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "model", "cached_hit", "input_tokens", "output_tokens", "updated_at")
    search_fields = ("instruction", "prompt", "response_md", "request_hash")
    list_filter = ("model", "cached_hit")

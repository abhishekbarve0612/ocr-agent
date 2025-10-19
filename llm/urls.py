# llm/urls.py
from django.urls import path
from .views import generate

app_name = 'llm'

urlpatterns = [
    path("generate", generate, name="generate"),
]

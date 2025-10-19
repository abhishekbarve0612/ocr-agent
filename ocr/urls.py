from django.urls import path
from . import views

app_name = 'ocr'

urlpatterns = [
    path('start/<int:file_id>/', views.start_ocr, name='start'),
    path('document/<int:file_id>/', views.document_detail, name='document_detail'),
]
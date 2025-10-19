from django.urls import path
from . import views

app_name = 'uploads'

urlpatterns = [
    path('', views.upload_file, name='file'),
    path('delete/<int:file_id>/', views.delete_file, name='delete'),
]
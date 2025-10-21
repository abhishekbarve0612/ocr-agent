from django.urls import path
from . import views

app_name = 'formatter'

urlpatterns = [
    path('start/<int:document_id>/', views.formatter_form, name='start'),
    path('run/<int:run_id>/', views.formatter_run_detail, name='run_detail'),
    path('run/<int:run_id>/download/', views.formatter_run_download, name='run_download'),
]

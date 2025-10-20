from django.urls import path
from . import views

app_name = 'formatter'

urlpatterns = [
    path('start/<int:document_id>/', views.formatter_form, name='start'),
]

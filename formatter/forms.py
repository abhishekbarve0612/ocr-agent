from django import forms
from uploads.models import UploadedFile

class FormatterForm(forms.Form):
    document = forms.ModelChoiceField(queryset=UploadedFile.objects.all(), editable=False)
    prompt = forms.CharField(widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}), max_length=1000, required=True)
    

from django import forms

from ocr.models import OCRDocument

class FormatterForm(forms.Form):
    document = forms.ModelChoiceField(
        queryset=OCRDocument.objects.filter(status=OCRDocument.Status.COMPLETED).order_by('-created_at').first(),
        widget=forms.HiddenInput(),
    )
    prompt = forms.CharField(widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}), max_length=1000, required=True)

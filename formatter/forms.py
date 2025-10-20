from django import forms

from ocr.models import OCRDocument

class FormatterForm(forms.Form):
    document = forms.ModelChoiceField(
        queryset=OCRDocument.objects.none(),
        widget=forms.HiddenInput(),
    )
    prompt = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 10, 'cols': 80}),
        max_length=1000,
        required=True,
    )

    def __init__(self, *args, document: OCRDocument | None = None, **kwargs):
        super().__init__(*args, **kwargs)
        queryset = OCRDocument.objects.all()
        if document is not None:
            queryset = queryset.filter(pk=document.pk)
            self.initial.setdefault('document', document.pk)
        self.fields['document'].queryset = queryset

from django import forms
from .models import OCRDocument

class OCRStartForm(forms.Form):
    page_range = forms.CharField(
        required=False,
        help_text="e.g. 'all', '1-10', '1,3,5-7', '1-3,5', Leave blank to process all pages",
    )
    
    languages = forms.ChoiceField(
        required=False,
        choices=OCRDocument.Language.choices,
        help_text="Select the languages to process. Leave blank to process all languages",
    )
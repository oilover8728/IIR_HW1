from django import forms

class UploadDocumentForm(forms.Form):
    file = forms.FileField(label='', required=True)
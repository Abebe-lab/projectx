from django.utils import timezone
from django import forms
from django.contrib.auth.models import User
from .models import Document  # Ensure you import your Document model

class DocumentForm(forms.ModelForm):
    shared_with = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple  # Optional: Change to your preferred widget
    )
    # keywords = forms.CharField(widget=forms.Textarea(attrs={'rows': 5}), required=False)
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 5}), required=False)
    # Make document_date readonly
    uploaded_date = forms.DateField(initial=timezone.now().date, widget=forms.DateInput(attrs={'type': 'date', 'readonly': 'readonly'}), required=True)

    class Meta:
        model = Document
        exclude = ['object_id', 'uploaded_by']

    def __init__(self, *args, **kwargs):
        super(DocumentForm, self).__init__(*args, **kwargs)

        # Add Bootstrap classes to the form fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

from django import forms
from .models import ExternalCustomer
from django.utils.safestring import mark_safe


class CustomerForm(forms.ModelForm):
    name_en = forms.CharField(required=True, label=mark_safe("Name (en) <span style='color: red'>*</span>"),
                              widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "English Name"}))
    name_am = forms.CharField(required=True, label=mark_safe("የአማርኛ ስም <span style='color: red'>*</span>"),
                              widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "የአማርኛ ስም"}))
    description = forms.CharField(required=False, label="Description",
                                  widget=forms.Textarea(attrs={"class": "form-control", "placeholder": "Description", "rows": 4,  "style": "width: 100%;"}))

    contact = forms.CharField(required=False, label="Contact",
                              widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Contact"}))
    customer_type = forms.ChoiceField(choices=[('', 'Select Customer Type'), ('Org', 'Organization'),
                                               ('Ind', 'Individual')], required=True, label=mark_safe("Customer Type <span style='color: red'>*</span>"),
                                      widget=forms.Select(attrs={"class": "form-select", "placeholder": "Customer Type"}))

    class Meta:
        model = ExternalCustomer
        fields = ['name_en', 'name_am', 'customer_type', 'description', 'contact']

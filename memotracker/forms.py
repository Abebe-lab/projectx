from django import forms
from django.core.files.storage import FileSystemStorage
from django.forms import ModelForm, ChoiceField, CheckboxSelectMultiple
from django.shortcuts import get_object_or_404
from django.contrib.contenttypes.models import ContentType
from .models import Memo, MemoRoute, ApprovalRoute, MemoAttachment, Document, MemoAction
from ckeditor.widgets import CKEditorWidget
from django.contrib.auth.models import User

from organogram.models import UserRole, ExternalCustomer, BusinessUnit


class MemoSearchForm(forms.Form):
    subject = forms.CharField(max_length=300)
    memo_date = forms.DateTimeField()

class MemoForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorWidget(attrs={'id': 'memoContent'}))
    memo_date=forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    due_date=forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    document = ChoiceField(choices=[], required=False)
    permission = ChoiceField(choices=[], required=False)
    class Meta:
        model = Memo
        exclude = ['object_id', 'created_by', 'keywords', 'status']

    def __init__(self, *args, **kwargs):
        self.user_id = kwargs.pop('user_id', None)
        self.bunit_id = kwargs.pop('bunit_id', None)
        self.org_list = kwargs.pop('org_list', None)
        super(MemoForm, self).__init__(*args, **kwargs)
        self.fields["document"].choices = [
            (document.pk, document.title) for document in Document.objects.all()
        ]
        self.fields["permission"].choices = [('read', 'Read'),('share', 'Share'),]
         # Add Bootstrap classes to the form fields
        for field_name, field in self.fields.items():
            if(field_name == 'urgent' or field_name == 'public' or field_name == 'to_external' or field_name == 'in_english'):
                field.widget.attrs['class'] = 'form-check-input'
            elif(field_name == 'content_type' or field_name == 'assigned_to'):
                field.widget.attrs['class'] = 'form-select'
            else:
                field.widget.attrs['class'] = 'form-control'
            
            if(field_name=='assigned_to'):
                field.empty_label="--- Select staff ---"
                field.queryset = User.objects.filter(userrole__business_unit_id=self.bunit_id).exclude(userrole__user_id=self.user_id)
            if(field_name=='content_type'):
                field.empty_label = None
                

    def save(self, commit=True):
        if commit:
            content_type_str = str(self.cleaned_data['content_type'])
            app_label, model_name = content_type_str.split(' | ')

            if model_name == 'user':
                object_id = self.user_id
            elif model_name == 'business unit':
                object_id = self.bunit_id
            else:
                object_id = self.org_list.filter(name_en=self.cleaned_data['content_type']).first().id

            self.instance.object_id = object_id

        return super().save(commit=commit)



class ExternalMemoForm(forms.ModelForm):
    content = forms.CharField(widget=CKEditorWidget(), required=False)
    memo_date = forms.DateField(widget=forms.DateInput(attrs={'type': 'date'}))
    customer = forms.ModelChoiceField(queryset=ExternalCustomer.objects.all(), required=True)  # Change here
    document = forms.ChoiceField(choices=[], required=False)  # Change here
    permission = forms.ChoiceField(choices=[], required=False)
    class Meta:
        model = Memo
        exclude = ['content_type', 'priority', 'privacy', '', 'object_id', 'created_by', 'keywords', 'status']

    def __init__(self, *args, **kwargs):
        self.user_id = kwargs.pop('user_id', None)
        self.bunit_id = kwargs.pop('bunit_id', None)
        self.org_list = kwargs.pop('org_list', None)
        super(ExternalMemoForm, self).__init__(*args, **kwargs)
        self.fields["document"].choices = [(document.id, document.title) for document in Document.objects.all()]
        self.fields["permission"].choices = [('read', 'Read'), ('share', 'Share')]
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'
            if(field_name == 'in_english'):
                field.widget.attrs['class'] = 'form-check-input'

    def save(self, commit=True):
        if commit:
            object_id = self.org_list.filter(name_en=self.cleaned_data['content_type']).first().id
            self.instance.object_id = object_id

        return super().save(commit=commit)
class RoutingModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(RoutingModelForm, self).__init__(*args, **kwargs)
        initial = kwargs.get('initial', {})
        self.fields['form_type'].initial = initial.get('form_type')
        self.fields['current_user_bu'].initial = initial.get('current_user_bu')
        if initial.get('form_type') != "Approval Route" and initial.get('form_type') != "Route Cc":
            self.fields['manager'].initial = initial.get('is_manager')
            self.fields['delegate'].initial = initial.get('is_delegate')
        if initial.get('form_type') != "Route Cc":
            self.fields['memo'].initial = initial.get('memo')
            self.fields['memo_status'].initial = initial.get('memo_status')
            self.fields['from_user'].initial = initial.get('from_user')
            self.fields['content_type_routing'].initial = initial.get('content_type')
            self.fields['is_to_external'].initial = initial.get('is_to_external')
        if initial.get('form_type') == 'Memo Route-Edit to User':
            self.fields['to_user'].initial = initial.get('destination_id')
        if initial.get('form_type') == 'Memo Route-Edit to Business Unit':
            self.fields['business_unit'].initial = initial.get('destination_id')
        if initial.get('form_type') == 'Memo Route-Edit to External':
            self.fields['external'].initial = initial.get('external')
        else:
            self.fields['business_unit'].initial = initial.get('department')
            self.fields['business_unit2'].initial = initial.get('department')
        if initial.get('title') == 'Edit Memo Route' or initial.get('title') == 'Edit Memo Approval':
            self.fields['to_user_list'].initial = initial.get('to_user')
            if initial.get('title') == 'Edit Memo Route':
                self.fields['memo_action'].initial = initial.get('memo_action')
                self.fields['remark'].initial = initial.get('remark')
                self.fields['carbon_copy'].initial = initial.get('carbon_copy')
            if initial.get('title') == 'Edit Memo Approval':
                self.fields['comment'].initial = initial.get('comment')

    class Meta:
        model = None
        fields = None


class MemoRouteForm(RoutingModelForm):

    def __init__(self, *args, **kwargs):
        current_user = kwargs.pop('current_user')
        super().__init__(*args, **kwargs)
        # self.fields['business_unit'].widget.attrs['onchange'] = 'getBusinessUnitUser()'

    form_type = forms.CharField(max_length=300, required=False, widget=forms.HiddenInput(attrs={"id": "formType"}))
    manager = forms.BooleanField(required=False, widget=forms.HiddenInput(attrs={"id": "isManager"}))
    delegate = forms.BooleanField(required=False, widget=forms.HiddenInput(attrs={"id": "isDelegate"}))
    level = forms.IntegerField(required=False, widget=forms.HiddenInput(attrs={"value": 1}))
    memo = forms.ModelChoiceField(queryset=Memo.objects.all(), widget=forms.HiddenInput())
    memo_status = forms.CharField(max_length=300, required=False, widget=forms.HiddenInput(attrs={"id": "memoStatus"}))
    current_user_bu = forms.CharField(max_length=300, required=False, widget=forms.HiddenInput(attrs={"id": "currentUserBu"}))
    content_type_routing = forms.CharField(max_length=300, required=False, widget=forms.HiddenInput(attrs={"id": "memoContentType"}))
    is_to_external = forms.BooleanField(required=False, widget=forms.HiddenInput(attrs={"id": "isToExternal"}))
    from_user = forms.ModelChoiceField(queryset=User.objects.all(), required=True, empty_label="Select User",
                                       widget=forms.HiddenInput())
    external = forms.ModelChoiceField(queryset=ExternalCustomer.objects.all(), required=False, empty_label=None,
                                      label="External Customer",
                                      widget=forms.Select(attrs={"class": "form-select", "id": "routingExternal", "multiple": ""}))
    business_unit = forms.ModelChoiceField(queryset=BusinessUnit.objects.all(), required=False, empty_label=None, label="Business Unit",
                                           widget=forms.Select(attrs={"class": "form-select", "id": "routingBU", "multiple": ""}))
    business_unit2 = forms.ModelChoiceField(queryset=BusinessUnit.objects.all(), required=False, empty_label=None,
                                           label="Business Unit",
                                           widget=forms.Select(attrs={"class": "form-select", "id": "routingBU2"}))
    to_user = forms.ModelChoiceField(queryset=User.objects.all(), required=False, empty_label=None, label="To User",
                                     widget=forms.Select(attrs={"class": "form-select", "id": "routingToUser", "multiple": ""}))
    to_user_list = forms.CharField(max_length=300, required=False, widget=forms.HiddenInput(attrs={"class": "form-select", "id": "routingToUserInputList"}))
    to_bu_list = forms.CharField(max_length=300, required=False, widget=forms.HiddenInput(attrs={"id": "toBuInputList"}))
    carbon_copy = forms.BooleanField(initial=False, label="Carbon Copy", required=False,
                                     widget=forms.CheckboxInput(attrs={"style": "width: 15px; height: 15px;"}))
    carbon_copy_list = forms.CharField(max_length=300, required=False, widget=forms.HiddenInput(attrs={"id": "routingCarbonCopyInputList"}))
    bu_carbon_copy_list = forms.CharField(max_length=300, required=False,
                                       widget=forms.HiddenInput(attrs={"id": "routingBuCarbonCopyInputList"}))
    memo_action = forms.ModelChoiceField(queryset=MemoAction.objects.all(), required=False, empty_label="Select Actions", label="Actions",
                                         widget=forms.Select(attrs={"class": "form-select", "id": "memoAction"}))
    remark = forms.CharField(required=False, label="Remark",
                             widget=forms.Textarea(attrs={"class": "form-control", "placeholder": "Remark", "rows": 4}))

    class Meta:
        model = MemoRoute
        fields = ['memo', 'level', 'from_user', 'business_unit', 'carbon_copy', 'memo_action', 'remark']


class MemoRouteCcForm(RoutingModelForm):

    def __init__(self, *args, **kwargs):
        current_user = kwargs.pop('current_user')
        super().__init__(*args, **kwargs)
        self.fields['business_unit'].widget.attrs['onchange'] = 'getBusinessUnitUser()'

    business_unit = forms.ModelChoiceField(queryset=BusinessUnit.objects.all(), required=True, empty_label="Select Business Unit", label="Business Unit",
                                           widget=forms.Select(attrs={"class": "form-select", "id": "routingCcBU"}))
    to_user = forms.ModelChoiceField(queryset=User.objects.all(), required=False, empty_label="Select User", label="User",
                                     widget=forms.Select(attrs={"class": "form-select", "id": "routingCcToUser"}))
    to_user_list = forms.CharField(max_length=300, required=False, widget=forms.HiddenInput(attrs={"id": "routingCcToUserInputList"}))

    class Meta:
        model = MemoRoute
        fields = ['business_unit', 'to_user']

class ApprovalRouteForm(RoutingModelForm):
    def __init__(self, *args, **kwargs):
        current_user = kwargs.pop('current_user')
        super().__init__(*args, **kwargs)
        user_role = get_object_or_404(UserRole, user=current_user)
        business_unit_id = user_role.business_unit_id
        self.fields['to_user'].queryset = User.objects.filter(userrole__business_unit_id=business_unit_id).exclude(id=current_user.id)

    form_type = forms.CharField(max_length=300, required=False, widget=forms.HiddenInput(attrs={"id": "formType"}))
    memo = forms.ModelChoiceField(queryset=Memo.objects.all(), widget=forms.HiddenInput())
    memo_status = forms.CharField(max_length=300, required=False, widget=forms.HiddenInput(attrs={"id": "memoStatus"}))
    current_user_bu = forms.CharField(max_length=300, required=False,
                                      widget=forms.HiddenInput(attrs={"id": "currentUserBu"}))
    content_type_routing = forms.CharField(max_length=300, required=False, widget=forms.HiddenInput(attrs={"class": "form-control"}))
    is_to_external = forms.BooleanField(required=False, widget=forms.HiddenInput(attrs={"id": "isToExternal"}))
    from_user = forms.ModelChoiceField(queryset=User.objects.all(), required=False, empty_label="Select User",
                                       widget=forms.HiddenInput())
    external = forms.ModelChoiceField(queryset=ExternalCustomer.objects.all(), required=False, empty_label=None,
                                      label="External Customer",
                                      widget=forms.Select(
                                          attrs={"class": "form-select", "id": "routingExternal", "multiple": ""}))
    business_unit = forms.ModelChoiceField(queryset=BusinessUnit.objects.all(), required=False,
                                           empty_label="Select Business Unit", label="Business Unit",
                                           widget=forms.HiddenInput(attrs={"id": "routingBU"}))
    business_unit2 = forms.ModelChoiceField(queryset=BusinessUnit.objects.all(), required=False, empty_label=None,
                                            label="Business Unit",
                                            widget=forms.Select(attrs={"class": "form-select", "id": "routingBU2"}))
    to_user = forms.ModelChoiceField(queryset=User.objects.none(), required=True, empty_label="Select User",
                                     widget=forms.Select(attrs={"class": "form-select", "id": "routingToUser"}))
    to_user_list = forms.CharField(max_length=300, required=False,
                                   widget=forms.HiddenInput(attrs={"class": "form-select", "id": "routingToUserInputList"}))
    comment = forms.CharField(required=False, label="",
                              widget=forms.Textarea(attrs={"class": "form-control", "placeholder": "Comment",
                                                           'maxlength': '100', 'id': 'approval_comment'}))

    class Meta:
        model = ApprovalRoute
        fields = ['memo', 'from_user', 'to_user', 'comment']


class MemoAttachmentForm(ModelForm):
    class Meta:
        model = MemoAttachment
        fields = ['document', 'permission', 'remark']
        widgets = {
            'remark': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        memo_id=kwargs.pop('memo_id', None)
        super(MemoAttachmentForm, self).__init__(*args, **kwargs)

        #set the memo id to be the memo id of the current memo
        if memo_id:
            self.instance.memo=Memo.objects.get(pk=memo_id)
        #self.fields['attached_by'].initial = self.instance.memo.owner

         # Add Bootstrap classes to the form fields
        for field_name, field in self.fields.items():
            field.widget.attrs['class'] = 'form-control'

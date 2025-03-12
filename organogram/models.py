from django.db import models
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django import forms
from projectx import settings


# Create your models here.
class Category(models.Model):
    name = models.CharField(max_length=200)
    description = models.CharField(max_length=300)

    class Meta:
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name


class BusinessUnit(models.Model):
    code = models.CharField(max_length=10)
    name_am = models.CharField(verbose_name='Name(am)', max_length=200)
    name_en = models.CharField(verbose_name='Name(en)', max_length=200)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='children')
    category = models.ForeignKey(Category, null=True, blank=True, on_delete=models.SET_NULL)
    bu_signature = models.ImageField(upload_to='digital_signature/', blank=True, null=True)
    location = models.CharField(max_length=150)
    contact = models.CharField(max_length=100)
    last_memo_ref_number = models.IntegerField(default=0)
    # New fields for headers and footers
    internal_header_image = models.ImageField(upload_to='headers/internal/', blank=True, null=True)
    external_header_image = models.ImageField(upload_to='headers/external/', blank=True, null=True)
    internal_footer_image = models.ImageField(upload_to='footers/internal/', blank=True, null=True)
    external_footer_image = models.ImageField(upload_to='footers/external/', blank=True, null=True)
    class Meta:
        ordering = ['name_en']

    def __str__(self):
        return f"{self.code} - {self.name_en}"

class Role(models.Model):
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=300)
    is_manager = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    
class UserRole(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    business_unit = models.ForeignKey(BusinessUnit, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    active = models.BooleanField()
    deligated = models.BooleanField()

    def __str__(self):
        return self.user.username + ' - ' + self.role.name + ' - ' + self.business_unit.code

class ExternalCustomer(models.Model):
    name_am = models.CharField(verbose_name='Name(am)', max_length=200)
    name_en = models.CharField(verbose_name='Name(en)', max_length=200)
    description = models.CharField(max_length=300, blank=True, null=True)
    contact = models.CharField(max_length=100, blank=True, null=True)
    customer_type = models.CharField(choices = [
        ('Org', 'Organization'),
        ('Ind', 'Individual'),
    ])

    class Meta:
        ordering = ['name_en']

    def __str__(self):
        return self.name_en + ' - ' + self.name_am

CUSTOM_DISPLAY_NAMES = {
    'user': 'Personal',
    'businessunit': 'Business Unit',
    'externalcustomer': 'External',
}

class CustomModelNameChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        model_name = obj.model.lower()
        return CUSTOM_DISPLAY_NAMES.get(model_name, obj.model)

class ContentTypeModelField(models.ForeignKey):
    def formfield(self, **kwargs):
        defaults = {
            'form_class': CustomModelNameChoiceField,
            'queryset': ContentType.objects.filter(
                models.Q(app_label='auth', model='user') |
                models.Q(app_label='organogram', model='businessunit') |
                models.Q(app_label='organogram', model='externalcustomer')
            )
        }
        defaults.update(kwargs)
        return super().formfield(**defaults)

class PermissionParent(models.Model):
    code = models.CharField(max_length=10)
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
class Permission(models.Model):
    name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=100, blank=True)
    display_name = models.CharField(max_length=50)
    icon = models.CharField(max_length=50)
    url = models.CharField(max_length=100)
    parent = models.ForeignKey(PermissionParent,blank=True, null=True, on_delete=models.SET_NULL)
    order = models.IntegerField(default=0)

    def __str__(self):
        return self.display_name


class RolePermission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE)

    class Meta:
        ordering = ['permission__order']
    def __str__(self):
        return self.role.name + ' - ' + self.permission.name
class Profile(models.Model):
    SECURITY_QUESTIONS = [
        ("Your birth year", "Your birth year"),
        ("Your grandmother's name", "Your grandmother's name"),
        ("Name of your elementary school", "Name of your elementary school"),
        ("Your favorite color", "Your favorite color"),
        ("Your first pet's name", "Your first pet's name"),
        ("City where you were born", "City where you were born"),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=150, blank=True)
    full_name_am = models.CharField(max_length=150, blank=True) ########
    pin_code = models.CharField(max_length=128, null=True)
    bio = models.TextField(max_length=500, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(upload_to=settings.DOCUMENT_PATH)
    password_set = models.BooleanField(default=False)
    preference = models.JSONField(default=dict)
    security_question_1 = models.CharField(max_length=100, choices=SECURITY_QUESTIONS, default="Your birth year")
    security_answer_1 = models.CharField(max_length=100, null=True, blank=True)
    security_question_2 = models.CharField(max_length=100, choices=SECURITY_QUESTIONS, null=True, blank=True,
                                               default="Your grandmother's name")
    security_answer_2 = models.CharField(max_length=100, null=True, blank=True)
    security_question_3 = models.CharField(max_length=100, choices=SECURITY_QUESTIONS, null=True, blank=True,
                                               default="Name of your elementary school")
    security_answer_3 = models.CharField(max_length=100, null=True, blank=True)
    last_personal_memo_ref_number = models.IntegerField(default=0)

    # Add more fields as per your requirements

    def __str__(self):
        return self.user.username
from django import forms
from django.contrib.auth.models import User
from organogram.models import Profile
from django.contrib.auth.forms import PasswordChangeForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


# class UserForm(forms.ModelForm):
#     class Meta:
#         model = User
#         fields = ('username', 'email')
#
# class ProfileForm(forms.ModelForm):
#     class Meta:
#         model = Profile
#         fields = ('bio', 'profile_picture')
#         exclude = ('birth_date', 'user')
#         labels = {
#             'bio': 'Bio',
#             'profile_picture': 'Profile',
#         }
#     def __init__(self, *args, **kwargs):
#         super(ProfileForm, self).__init__(*args, **kwargs)
#         self.fields['bio'].widget.attrs.update({'rows': 6, 'cols': 40})  # Set the size of the textarea


# from .models import Profile

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ('username', 'email')

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('bio', 'profile_picture', 'full_name_am')  # Include Amharic name field
        exclude = ('birth_date', 'user')
        labels = {
            'bio': 'Bio (English)',
            'profile_picture': 'Profile Picture',
            'full_name_am': 'Full Name (Amharic)',
        }

    def __init__(self, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        self.fields['bio'].widget.attrs.update({'rows': 6, 'cols': 40})  # Set size for English bio


class CustomPasswordChangeForm(PasswordChangeForm):
    def clean_new_password1(self):
        password1 = self.cleaned_data.get('new_password1')
        if len(password1) < 8:
            raise ValidationError(_("Your password must contain at least 8 characters."), code='password_too_short')
        if password1.isdigit():
            raise ValidationError(_("Your password can’t be entirely numeric."), code='password_entirely_numeric')
        return password1






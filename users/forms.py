from django import forms
from users.models import *
from django.contrib.auth.forms import UserCreationForm


class UserRegistrationForm(UserCreationForm):
    class Meta:
        model=User
        fields=["first_name","email","role","username","phone","password1","password2"]

class UserLoginFrom(forms.Form):
    username = forms.CharField(max_length=100)
    password = forms.CharField(max_length=100)


class VendorProfileForm(forms.ModelForm):
    class Meta:
        model = VendorProfile
        fields = "__all__"
        exclude = ["user"]
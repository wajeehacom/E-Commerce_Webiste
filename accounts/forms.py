from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import UserProfile


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['phone', 'address']
        widgets = {
            'phone': forms.TextInput(
                attrs={'placeholder': 'Phone', 'class': 'form-control'}
            ),
            'address': forms.Textarea(
                attrs={'rows': 3, 'placeholder': 'Address', 'class': 'form-control'}
            ),
        }
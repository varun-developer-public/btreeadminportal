from django.contrib.auth.forms import AuthenticationForm
from django import forms
from .models import CustomUser

class UserForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['name', 'email', 'role', 'password', 'is_staff', 'is_superuser']
        widgets = {
            'password': forms.PasswordInput(),
        }
        # These fields are for UI display; logic is handled in save()
        extra_kwargs = {
            'is_staff': {'required': False},
            'is_superuser': {'required': False}
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        role = self.cleaned_data.get('role')
        
        if role == 'admin':
            user.is_staff = True
            user.is_superuser = True
        elif role == 'student':
            user.is_staff = False
            user.is_superuser = False
        else: # For all other staff-level roles
            user.is_staff = True
            user.is_superuser = False
            
        if commit:
            user.save()
        return user

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['name', 'email', 'role', 'is_staff', 'is_superuser']
        # These fields are for UI display; logic is handled in save()
        extra_kwargs = {
            'is_staff': {'required': False},
            'is_superuser': {'required': False}
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        role = self.cleaned_data.get('role')

        if role == 'admin':
            user.is_staff = True
            user.is_superuser = True
        elif role == 'student':
            user.is_staff = False
            user.is_superuser = False
        else: # For all other staff-level roles
            user.is_staff = True
            user.is_superuser = False
            
        if commit:
            user.save()
class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'autofocus': True})
    )
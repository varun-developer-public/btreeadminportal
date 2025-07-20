from django.contrib.auth.forms import AuthenticationForm
from django import forms
from .models import CustomUser
from consultantdb.models import Consultant, ConsultantProfile

class UserForm(forms.ModelForm):
    consultant = forms.ModelChoiceField(
        queryset=Consultant.objects.all(),
        required=False,
        help_text="Select a consultant only if the role is 'Consultant'."
    )

    class Meta:
        model = CustomUser
        fields = ['name', 'email', 'role', 'password', 'profile_picture', 'consultant', 'is_staff', 'is_superuser']
        widgets = {
            'password': forms.PasswordInput(),
        }
        # These fields are for UI display; logic is handled in save()
        extra_kwargs = {
            'is_staff': {'required': False},
            'is_superuser': {'required': False}
        }

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get("role")
        consultant = cleaned_data.get("consultant")

        if role == 'consultant' and not consultant:
            raise forms.ValidationError("A consultant must be selected for the 'Consultant' role.")
        
        if role != 'consultant' and consultant:
            raise forms.ValidationError("A consultant should only be selected for the 'Consultant' role.")

        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        role = self.cleaned_data.get('role')
        consultant = self.cleaned_data.get('consultant')

        if role == 'consultant' and consultant:
            user.email = consultant.email

        if role == 'admin':
            user.is_staff = True
            user.is_superuser = True
        elif role == 'staff':
            user.is_staff = True
            user.is_superuser = False
        else:  # For all other non-staff roles
            user.is_staff = False
            user.is_superuser = False
            
        if commit:
            user.save()
            if user.role == 'consultant':
                ConsultantProfile.objects.create(user=user, consultant=consultant)
        return user

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['name', 'email', 'role', 'profile_picture', 'is_staff', 'is_superuser']
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
        elif role == 'staff':
            user.is_staff = True
            user.is_superuser = False
        else:  # For all other non-staff roles
            user.is_staff = False
            user.is_superuser = False
            
        if commit:
            user.save()
class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'autofocus': True})
    )
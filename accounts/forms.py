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

    def __init__(self, *args, **kwargs):
        # Pop the 'user' from kwargs before calling super(), as the ModelForm
        # doesn't expect it.
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # If the user is not an admin, they cannot change the role or permissions.
        # We remove the fields from the form entirely to prevent them from
        # being submitted or processed.
        if self.user and self.user.role != 'admin':
            del self.fields['role']
            del self.fields['is_staff']
            del self.fields['is_superuser']

    def save(self, commit=True):
        # Explicitly handle the clearing of the profile picture. If the user
        # ticks the "clear" checkbox, the value for the field in cleaned_data
        # will be False.
        if self.cleaned_data.get('profile_picture') is False:
            # We set the profile_picture on the model instance to None.
            self.instance.profile_picture = None
        
        # Now we can call the parent's save() method. It will handle saving
        # a newly uploaded file or persisting the cleared (None) value.
        return super().save(commit=commit)
class EmailAuthenticationForm(AuthenticationForm):
    username = forms.EmailField(
        label="Email",
        widget=forms.EmailInput(attrs={'autofocus': True})
    )

from django.contrib.auth.forms import PasswordChangeForm as AuthPasswordChangeForm

class PasswordChangeForm(AuthPasswordChangeForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs.update({'class': 'form-control'})
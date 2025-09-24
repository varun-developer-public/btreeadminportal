from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django import forms
from .models import CustomUser
from consultantdb.models import Consultant, ConsultantProfile
from django.contrib.auth.forms import ReadOnlyPasswordHashField

class CustomUserCreationForm(forms.ModelForm):
    name = forms.CharField(label='Full Name')
    role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES)
    password1 = forms.CharField(label='Password', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirm Password', widget=forms.PasswordInput)
    consultant = forms.ModelChoiceField(
        queryset=Consultant.objects.all(),
        required=False,
        help_text="Select a consultant only if the role is 'Consultant'."
    )

    class Meta:
        model = CustomUser
        fields = ('email', 'name', 'role', 'consultant', 'profile_picture', 'is_staff', 'is_superuser')

    def clean(self):
        cleaned_data = super().clean()
        role = cleaned_data.get("role")
        consultant = cleaned_data.get("consultant")

        if role == 'consultant' and not consultant:
            raise forms.ValidationError("A consultant must be selected for the 'Consultant' role.")
        
        if role != 'consultant' and consultant:
            raise forms.ValidationError("A consultant should only be selected for the 'Consultant' role.")

        return cleaned_data

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Passwords don't match")
        return password2

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            if user.role == 'consultant':
                consultant = self.cleaned_data.get('consultant')
                ConsultantProfile.objects.create(user=user, consultant=consultant)
        return user

class CustomUserAdmin(UserAdmin):
    add_form = CustomUserCreationForm
    model = CustomUser
    list_display = ('email', 'name', 'role', 'is_staff', 'is_superuser',)
    list_filter = ('role','is_staff', 'is_superuser')
    ordering = ('email',)
    search_fields = ('email', 'name')
    
    fieldsets = (
        (None, {'fields': ('email', 'name', 'password',)}),
        ('Role Info', {'fields': ('role',)}),
        ('Permissions', {'fields': ('is_staff', 'is_superuser', 'groups', 'user_permissions')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'name', 'role', 'password1', 'password2', 'is_staff', 'is_superuser')}
        ),
    )


admin.site.register(CustomUser, CustomUserAdmin)

from django import forms
from .models import Company, ApplyingRole
from coursedb.models import Course

class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['portal', 'company_name', 'spoc', 'mobile', 'email', 'location']
        widgets = {
            'portal': forms.TextInput(attrs={'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'spoc': forms.TextInput(attrs={'class': 'form-control'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
        }

class ApplyingRoleForm(forms.ModelForm):
    courses = forms.ModelMultipleChoiceField(
        queryset=Course.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2'})
    )

    class Meta:
        model = ApplyingRole
        fields = ['role_name', 'courses', 'salary']
        widgets = {
            'role_name': forms.TextInput(attrs={'class': 'form-control'}),
            'salary': forms.TextInput(attrs={'class': 'form-control'}),
        }
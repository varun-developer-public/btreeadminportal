from django import forms
from .models import PlacementDrive

class PlacementDriveForm(forms.ModelForm):
    class Meta:
        model = PlacementDrive
        fields = ['portal', 'company_name', 'spoc', 'mobile', 'email', 'location']
        widgets = {
            'portal': forms.TextInput(attrs={'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
            'spoc': forms.TextInput(attrs={'class': 'form-control'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
        }
from django import forms
from .models import Consultant

class ConsultantForm(forms.ModelForm):
    class Meta:
        model = Consultant
        fields = ['name', 'phone_number', 'email', 'address', 'date_of_birth']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

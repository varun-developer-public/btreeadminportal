from django import forms
from .models import Consultant

class ConsultantForm(forms.ModelForm):
    class Meta:
        model = Consultant
        fields = ['name', 'phone_number', 'email']

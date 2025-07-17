from django import forms
from .models import Trainer

class TrainerForm(forms.ModelForm):
    class Meta:
        model = Trainer
        fields = ['name', 'phone', 'email', 'address', 'date_of_birth', 'trainer_type', 'stack']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

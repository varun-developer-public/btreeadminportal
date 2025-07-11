from django import forms
from .models import Placement

class PlacementUpdateForm(forms.ModelForm):
    class Meta:
        model = Placement
        fields = [
            'resume_link',
            'is_active',
            'feedback',
            'company_1',
            'company_2',
            'company_3',
            'company_4',
            'company_5',
        ]
        widgets = {
            'feedback': forms.Textarea(attrs={'rows': 3}),
        }

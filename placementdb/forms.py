from django import forms
from .models import Placement, CompanyInterview

class PlacementUpdateForm(forms.ModelForm):
    class Meta:
        model = Placement
        fields = [
            'resume_link',
            'is_active',
        ]
        widgets = {
            'resume_link': forms.FileInput(attrs={'class': 'form-control'}),
        }

class CompanyInterviewForm(forms.ModelForm):
    class Meta:
        model = CompanyInterview
        fields = ['company', 'applying_for', 'interview_date', 'interview_time', 'attended']
        widgets = {
            'interview_date': forms.DateInput(attrs={'type': 'date'}),
            'interview_time': forms.TimeInput(attrs={'type': 'time'}),
        }

from django import forms
from .models import Trainer
import json
from django_select2.forms import Select2Widget
from core.utils import get_country_code_choices

class TrainerForm(forms.ModelForm):
    country_code = forms.CharField(widget=forms.HiddenInput())
    timing_slots = forms.CharField(widget=forms.HiddenInput(), required=False)
    commercials = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Trainer
        fields = [
            'name', 'country_code', 'phone_number', 'email', 'location',
            'other_location', 'years_of_experience', 'stack', 'mode',
            'availability', 'employment_type', 'timing_slots', 'profile',
            'demo_link', 'commercials'
        ]
        widgets = {
            'stack': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'profile': forms.FileInput(attrs={'class': 'form-control'}),
            'demo_link': forms.URLInput(attrs={'class': 'form-control'}),
        }

    def clean_timing_slots(self):
        timing_slots_str = self.cleaned_data.get('timing_slots')
        if not timing_slots_str:
            return []
        
        try:
            timing_slots = json.loads(timing_slots_str)
            if not isinstance(timing_slots, list):
                raise forms.ValidationError("Invalid format for timing slots.")

            for slot in timing_slots:
                if not isinstance(slot, dict) or 'start_time' not in slot or 'end_time' not in slot:
                    raise forms.ValidationError("Each slot must have a start and end time.")
                if slot['start_time'] >= slot['end_time']:
                    raise forms.ValidationError("End time must be after start time.")
            
            return timing_slots
        except json.JSONDecodeError:
            raise forms.ValidationError("Invalid JSON in timing slots.")

    def clean_commercials(self):
        commercials_str = self.cleaned_data.get('commercials')
        if not commercials_str:
            return []
        
        try:
            commercials = json.loads(commercials_str)
            if not isinstance(commercials, list):
                raise forms.ValidationError("Invalid format for commercials.")

            for commercial in commercials:
                if 'commercial_type' not in commercial:
                    raise forms.ValidationError("Each commercial must have a type.")
            
            return commercials
        except json.JSONDecodeError:
            raise forms.ValidationError("Invalid JSON in commercials.")

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.timing_slots = self.cleaned_data.get('timing_slots', [])
        instance.commercials = self.cleaned_data.get('commercials', [])
        if commit:
            instance.save()
            self.save_m2m()
        return instance

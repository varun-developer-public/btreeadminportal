from django import forms
from .models import Trainer
import json
from core.utils import get_country_code_choices

class TrainerForm(forms.ModelForm):
    country_code = forms.CharField(widget=forms.HiddenInput(), required=False)
    timing_slots = forms.CharField(widget=forms.HiddenInput(), required=False)
    commercials = forms.CharField(widget=forms.HiddenInput(), required=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.initial['timing_slots'] = json.dumps(self.instance.timing_slots)
            self.initial['commercials'] = json.dumps(self.instance.commercials)

    class Meta:
        model = Trainer
        fields = [
            'name', 'country_code', 'phone_number', 'email', 'location',
            'other_location', 'years_of_experience', 'stack', 'employment_type', 'timing_slots', 'profile',
            'demo_link', 'commercials', 'is_active'
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
                if not isinstance(slot, dict) or 'start_time' not in slot or 'end_time' not in slot or 'mode' not in slot or 'availability' not in slot:
                    raise forms.ValidationError("Each slot must have a start time, end time, mode, and availability.")
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
        instance = super(TrainerForm, self).save(commit=False)
        instance.timing_slots = self.cleaned_data.get('timing_slots')
        instance.commercials = self.cleaned_data.get('commercials')
        if commit:
            instance.save()
            self.save_m2m()
        return instance


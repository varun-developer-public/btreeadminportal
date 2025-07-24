from django import forms
from .models import Batch
from studentsdb.models import Student
from trainersdb.models import Trainer

class BatchCreationForm(forms.ModelForm):
    batch_id = forms.CharField(
        widget=forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control'}),
        required=False
    )
    students = forms.ModelMultipleChoiceField(
        queryset=Student.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2'}),
        required=True
    )

    trainer = forms.ModelChoiceField(
        queryset=Trainer.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control select2'}),
        required=True
    )

    # Add "Custom Time" to the time_slot choices
    time_slot_choices = Batch.SLOT_CHOICES + [('custom', 'Custom Time')]
    time_slot = forms.ChoiceField(
        choices=time_slot_choices,
        widget=forms.Select(attrs={'class': 'form-control'}),
        required=True
    )

    # Non-model field for custom time
    custom_time_slot = forms.CharField(
        max_length=50,
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 7:00 PM - 8:30 PM'})
    )

    class Meta:
        model = Batch
        fields = [
            'batch_id', 'module_name', 'batch_type', 'trainer', 'start_date', 'end_date',
            'time_slot', 'custom_time_slot', 'students'
        ]
        widgets = {
            'module_name': forms.Select(attrs={'class': 'form-control select2'}),
            'batch_type': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        time_slot = cleaned_data.get('time_slot')
        custom_time_slot = cleaned_data.get('custom_time_slot')

        if time_slot == 'custom' and not custom_time_slot:
            self.add_error('custom_time_slot', 'This field is required when "Custom Time" is selected.')

        return cleaned_data
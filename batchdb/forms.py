from django import forms
from .models import Batch
from studentsdb.models import Student
from trainersdb.models import Trainer

class BatchForm(forms.ModelForm):
    students = forms.ModelMultipleChoiceField(
        queryset=Student.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=True
    )

    trainer = forms.ModelChoiceField(
        queryset=Trainer.objects.all(),
        required=True
    )

    class Meta:
        model = Batch
        fields = ['batch_id', 'students', 'trainer', 'slot_timings']

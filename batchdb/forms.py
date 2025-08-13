from datetime import datetime
from django import forms
from .models import Batch
from coursedb.models import Course, CourseCategory
from trainersdb.models import Trainer
from studentsdb.models import Student
import json

class BatchCreationForm(forms.ModelForm):
    course_category = forms.ModelChoiceField(
        queryset=CourseCategory.objects.all(),
        required=True,
        label="Course Category",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    days = forms.MultipleChoiceField(
        choices=[
            ('Monday', 'Monday'),
            ('Tuesday', 'Tuesday'),
            ('Wednesday', 'Wednesday'),
            ('Thursday', 'Thursday'),
            ('Friday', 'Friday'),
            ('Saturday', 'Saturday'),
            ('Sunday', 'Sunday'),
        ],
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    time_slot = forms.ChoiceField(
        choices=[],
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Batch
        fields = [
            'course_category', 
            'course',
            'trainer', 'students',
            'start_date', 'end_date', 'batch_type', 'days',
            'time_slot', 'hours_per_day'
        ]
        widgets = {
            'course': forms.Select(attrs={'class': 'form-control'}),
            'trainer': forms.Select(attrs={'class': 'form-control'}),
            'students': forms.SelectMultiple(attrs={'class': 'form-control', 'size': '10'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'readonly': True}),
            'batch_type': forms.Select(attrs={'class': 'form-control'}),
            'hours_per_day': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['start_date'].initial = datetime.today().date()
        self.fields['course'].queryset = Course.objects.none()
        self.fields['trainer'].queryset = Trainer.objects.none()
        self.fields['time_slot'].choices = []

        if 'course_category' in self.data:
            try:
                category_id = int(self.data.get('course_category'))
                self.fields['course'].queryset = Course.objects.filter(category_id=category_id).order_by('course_name')
            except (ValueError, TypeError):
                pass
        
        if 'course' in self.data:
            try:
                course_id = int(self.data.get('course'))
                self.fields['trainer'].queryset = Trainer.objects.filter(stack__id=course_id).order_by('name')
                self.fields['students'].queryset = Student.objects.filter(
                    course_id=course_id, course_status__in=['YTS', 'IP']
                ).order_by('first_name')
            except (ValueError, TypeError):
                pass
        
        if 'trainer' in self.data:
            try:
                trainer_id = int(self.data.get('trainer'))
                trainer = Trainer.objects.get(id=trainer_id)
                
                active_batches = Batch.objects.filter(trainer=trainer, batch_status='In Progress')
                taken_slots = [(b.start_time, b.end_time) for b in active_batches]

                if isinstance(trainer.timing_slots, list):
                    available_slots = [
                        slot for slot in trainer.timing_slots
                        if isinstance(slot, dict) and
                           (datetime.strptime(slot['start_time'], '%H:%M').time(), datetime.strptime(slot['end_time'], '%H:%M').time()) not in taken_slots
                    ]
                    self.fields['time_slot'].choices = [
                        (
                            f"{slot['start_time']}-{slot['end_time']}",
                            f"{datetime.strptime(slot['start_time'], '%H:%M').strftime('%I:%M %p')} - {datetime.strptime(slot['end_time'], '%H:%M').strftime('%I:%M %p')}"
                        )
                        for slot in available_slots
                    ]
            except (ValueError, TypeError, Trainer.DoesNotExist):
                pass


    def clean_time_slot(self):
        time_slot = self.cleaned_data.get('time_slot')
        if time_slot:
            try:
                start_time_str, end_time_str = time_slot.split('-')
                start_time = datetime.strptime(start_time_str, '%H:%M').time()
                end_time = datetime.strptime(end_time_str, '%H:%M').time()
                return start_time, end_time
            except (ValueError, TypeError):
                raise forms.ValidationError("Invalid time slot format.")
        return None

class BatchUpdateForm(forms.ModelForm):
    days = forms.MultipleChoiceField(
        choices=[
            ('Monday', 'Monday'),
            ('Tuesday', 'Tuesday'),
            ('Wednesday', 'Wednesday'),
            ('Thursday', 'Thursday'),
            ('Friday', 'Friday'),
            ('Saturday', 'Saturday'),
            ('Sunday', 'Sunday'),
        ],
        widget=forms.CheckboxSelectMultiple,
        required=False
    )

    class Meta:
        model = Batch
        fields = [
            'course',
            'trainer', 'students', 'start_date', 'end_date',
            'batch_type', 'days', 'batch_status', 'hours_per_day'
        ]
        widgets = {
            'course': forms.Select(attrs={'class': 'form-control'}),
            'trainer': forms.Select(attrs={'class': 'form-control'}),
            'students': forms.SelectMultiple(attrs={'class': 'form-control', 'size': '10'}),
            'start_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'readonly': True}),
            'batch_type': forms.Select(attrs={'class': 'form-control'}),
            'batch_status': forms.Select(attrs={'class': 'form-control'}),
            'hours_per_day': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance:
            self.fields['students'].queryset = Student.objects.filter(
                course_id=instance.course.id
            ).order_by('first_name')
            
            if instance.trainer:
                trainer = instance.trainer
                active_batches = Batch.objects.filter(trainer=trainer, batch_status='In Progress').exclude(pk=instance.pk)
                self.fields['time_slot'] = forms.ChoiceField(
                    choices=[],
                    required=True,
                    widget=forms.Select(attrs={'class': 'form-control'})
                )
                taken_slots = [(b.start_time, b.end_time) for b in active_batches]

                if isinstance(trainer.timing_slots, list):
                    available_slots = [
                        slot for slot in trainer.timing_slots
                        if isinstance(slot, dict) and
                           (datetime.strptime(slot['start_time'], '%H:%M').time(), datetime.strptime(slot['end_time'], '%H:%M').time()) not in taken_slots
                    ]
                    self.fields['time_slot'].choices = [
                        (
                            f"{slot['start_time']}-{slot['end_time']}",
                            f"{datetime.strptime(slot['start_time'], '%H:%M').strftime('%I:%M %p')} - {datetime.strptime(slot['end_time'], '%H:%M').strftime('%I:%M %p')}"
                        )
                        for slot in available_slots
                    ]

                if instance.start_time and instance.end_time:
                    current_slot = f"{instance.start_time.strftime('%H:%M')}-{instance.end_time.strftime('%H:%M')}"
                    current_slot_display = f"{instance.start_time.strftime('%I:%M %p')} - {instance.end_time.strftime('%I:%M %p')} (Current)"
                    if (current_slot, current_slot_display) not in self.fields['time_slot'].choices:
                        self.fields['time_slot'].choices.append((current_slot, current_slot_display))
                    self.fields['time_slot'].initial = current_slot


    def clean_time_slot(self):
        time_slot = self.cleaned_data.get('time_slot')
        if time_slot:
            try:
                start_time_str, end_time_str = time_slot.split('-')
                start_time = datetime.strptime(start_time_str, '%H:%M').time()
                end_time = datetime.strptime(end_time_str, '%H:%M').time()
                return start_time, end_time
            except (ValueError, TypeError):
                raise forms.ValidationError("Invalid time slot format.")
        return None

class BatchFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label="",
        widget=forms.TextInput(attrs={'placeholder': 'Search by Student, Batch ID...', 'class': 'form-control'})
    )
    
    course = forms.ModelMultipleChoiceField(
        queryset=Course.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': '5'}),
        label="Course"
    )

    trainer = forms.ModelMultipleChoiceField(
        queryset=Trainer.objects.all(),
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'form-control', 'size': '5'}),
        label="Trainer"
    )

    batch_status = forms.MultipleChoiceField(
        choices=Batch.STATUS_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
        label="Batch Status"
    )

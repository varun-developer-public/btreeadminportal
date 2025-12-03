from datetime import datetime
from django import forms
from .models import Batch, BatchStudent
from coursedb.models import Course, CourseCategory
from trainersdb.models import Trainer
from studentsdb.models import Student
from django_select2.forms import Select2MultipleWidget
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
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'readonly':True}),
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

                    # Get all students for this course
                    students_qs = Student.objects.filter(
                        course_id=course_id,
                        course_status__in=['YTS', 'IP']
                    ).order_by('first_name')

                    # Exclude students already in an active batch
                    active_student_ids = BatchStudent.objects.filter(
                        is_active=True
                    ).values_list('student_id', flat=True)

                    self.fields['students'].queryset = students_qs.exclude(id__in=active_student_ids)

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
    class Meta:
        model = Batch
        fields = ['batch_status', 'batch_percentage', 'end_date']
        widgets = {
            'batch_status': forms.Select(attrs={'class': 'form-control'}),
            'batch_percentage': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01', 
                'min': '0',
                'max': '100'
            }),
            'end_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
class BatchFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label="Search Input",
        widget=forms.TextInput(attrs={'placeholder': 'Search by Student, Batch ID...', 'class': 'form-control'})
    )
    
    course = forms.ModelMultipleChoiceField(
        queryset=Course.objects.all(),
        required=False,
        widget=Select2MultipleWidget(attrs={'class': 'form-control', 'data-placeholder': 'Select Courses'}),
        label="Course"
    )

    trainer = forms.ModelMultipleChoiceField(
        queryset=Trainer.objects.all(),
        required=False,
        widget=Select2MultipleWidget(attrs={'class': 'form-control', 'data-placeholder': 'Select Trainers'}),
        label="Trainer"
    )

    batch_status = forms.MultipleChoiceField(
        choices=Batch.STATUS_CHOICES,
        required=False,
        widget=Select2MultipleWidget(attrs={'class': 'form-control', 'data-placeholder': 'Select Statuses'}),
        label="Batch Status"
    )

    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label="Start Date"
    )

    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label="End Date"
    )

    time_slot = forms.ChoiceField(
        choices=[],
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Time Slot"
    )
    
    trainer_type = forms.ChoiceField(
        choices=[('', 'All')] + Trainer.EMPLOYMENT_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'}),
        label="Trainer Type"
    )

    percentage_min = forms.DecimalField(
        required=False,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Min %'}),
        label="Min %"
    )

    percentage_max = forms.DecimalField(
        required=False,
        min_value=0,
        max_value=100,
        widget=forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'placeholder': 'Max %'}),
        label="Max %"
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Get all unique time slots from all trainers
        all_slots = set()
        trainers = Trainer.objects.all()
        for trainer in trainers:
            if isinstance(trainer.timing_slots, list):
                for slot in trainer.timing_slots:
                    if isinstance(slot, dict) and 'start_time' in slot and 'end_time' in slot:
                        start_time = datetime.strptime(slot['start_time'], '%H:%M').strftime('%I:%M %p')
                        end_time = datetime.strptime(slot['end_time'], '%H:%M').strftime('%I:%M %p')
                        all_slots.add(f"{slot['start_time']}-{slot['end_time']}")

        # Create choices for the time_slot field
        slot_choices = [('', 'All Slots')] + [(slot, f"{datetime.strptime(slot.split('-')[0], '%H:%M').strftime('%I:%M %p')} - {datetime.strptime(slot.split('-')[1], '%H:%M').strftime('%I:%M %p')}") for slot in sorted(list(all_slots))]
        self.fields['time_slot'].choices = slot_choices

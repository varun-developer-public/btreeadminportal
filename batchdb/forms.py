from django import forms
from .models import Batch
from coursedb.models import CourseCategory, Course
from trainersdb.models import Trainer
from studentsdb.models import Student

class BatchCreationForm(forms.ModelForm):
    course_category = forms.ModelChoiceField(
        queryset=CourseCategory.objects.all(),
        label="Course Category",
        empty_label="Select a category",
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Batch
        fields = [
            'course', 'trainer', 'students', 'start_date', 'end_date',
            'time_slot', 'batch_days', 'hours_per_day',
        ]
        widgets = {
            'course': forms.Select(attrs={'class': 'form-control'}),
            'trainer': forms.Select(attrs={'class': 'form-control'}),
            'students': forms.SelectMultiple(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control', 'readonly': True}),
            'time_slot': forms.Select(attrs={'class': 'form-control'}),
            'batch_days': forms.CheckboxSelectMultiple(choices=[
                (1, 'Monday'), (2, 'Tuesday'), (3, 'Wednesday'),
                (4, 'Thursday'), (5, 'Friday'), (6, 'Saturday'),
                (0, 'Sunday')
            ]),
            'hours_per_day': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 8}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['course'].queryset = Course.objects.none()
        self.fields['trainer'].queryset = Trainer.objects.none()
        self.fields['students'].queryset = Student.objects.none()
        self.fields['time_slot'].choices = [("", "Select a trainer first")]

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
                    course_id=course_id,
                    course_status__in=['YTS', 'IP']
                ).order_by('first_name')
            except (ValueError, TypeError):
                pass

        if 'trainer' in self.data:
            try:
                trainer_id = int(self.data.get('trainer'))
                trainer = Trainer.objects.get(id=trainer_id)
                
                active_batches = Batch.objects.filter(trainer=trainer, batch_status='In Progress')
                taken_slots = [batch.time_slot for batch in active_batches]
                
                available_slots = [slot for slot in trainer.timing_slots if slot not in taken_slots]
                self.fields['time_slot'].choices = [(slot, slot) for slot in available_slots]
            except (ValueError, TypeError, Trainer.DoesNotExist):
                pass

class BatchUpdateForm(BatchCreationForm):
    class Meta(BatchCreationForm.Meta):
        fields = BatchCreationForm.Meta.fields + ['batch_status', 'batch_percentage']
        widgets = BatchCreationForm.Meta.widgets
        widgets.update({
            'batch_status': forms.Select(attrs={'class': 'form-control'}, choices=Batch.BATCH_STATUS_CHOICES),
            'batch_percentage': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'max': 100}),
        })

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        instance = kwargs.get('instance')
        if instance:
            self.fields['course_category'].initial = instance.course.category.id
            self.fields['course'].queryset = Course.objects.filter(category=instance.course.category)
            self.fields['trainer'].queryset = Trainer.objects.filter(stack=instance.course)
            self.fields['students'].queryset = Student.objects.filter(
                course=instance.course,
                course_status__in=['YTS', 'IP']
            )
            
            trainer = instance.trainer
            if trainer:
                active_batches = Batch.objects.filter(trainer=trainer, batch_status='In Progress').exclude(id=instance.id)
                taken_slots = [batch.time_slot for batch in active_batches]
                available_slots = [slot for slot in trainer.timing_slots if slot not in taken_slots]
                self.fields['time_slot'].choices = [(slot, slot) for slot in available_slots]

from django import forms
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from studentsdb.models import Student
from consultantdb.models import Consultant
from settingsdb.models import SourceOfJoining

class StudentForm(forms.ModelForm):
    source_of_joining = forms.ModelChoiceField(
        queryset=SourceOfJoining.objects.all(),
        required=False,
        empty_label="Select Source of Joining"
    )
    consultant = forms.ModelChoiceField(
        queryset=Consultant.objects.all(),
        required=False,
        empty_label="Select Consultant"
    )

    class Meta:
        model = Student
        fields = [
            'first_name', 'last_name', 'phone', 'alternative_phone', 'email',
            'date_of_birth', 'join_date', 'start_date', 'tentative_end_date',
            'course_percentage', 'pl_required', 'source_of_joining',
            'mode_of_class', 'week_type', 'consultant'
        ]
        widgets = {
            'join_date': forms.DateInput(attrs={
                'type': 'date',
                'readonly': 'readonly'
            }),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'tentative_end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = timezone.now().date()
        self.fields['join_date'].initial = today
        self.fields['start_date'].initial = today
        self.fields['tentative_end_date'].initial = today + relativedelta(months=4)


class StudentUpdateForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'first_name',
            'last_name',
            'phone',
            'alternative_phone',
            'email',
            'date_of_birth',
            'tentative_end_date',
            'course_percentage',
            'pl_required',
            'mode_of_class',
            'week_type',
        ]
        widgets = {
            'tentative_end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

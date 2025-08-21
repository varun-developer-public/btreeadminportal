from django import forms
from .models import Company, Interview, InterviewStudent
from coursedb.models import Course
from studentsdb.models import Student

class CompanyForm(forms.ModelForm):
    reason_for_not_conducting = forms.CharField(widget=forms.Textarea, required=False)
    class Meta:
        model = Company
        fields = [ 'portal', 'other_portal', 'company_name', 'spoc', 'mobile', 'email', 'location', 'date','other_location', 'progress','reason_for_not_conducting']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        self.request = kwargs.pop('request', None)
        # super().__init__(*args, **kwargs)

        # self.fields['date'].widget.attrs['readonly'] = True
        self.fields['date'].widget = forms.DateInput(attrs={'type': 'date'})
        if not self.instance.pk:
            self.fields['progress'].widget = forms.HiddenInput()
            self.fields['progress'].initial = 'resume_shared'

class InterviewScheduleForm(forms.ModelForm):
    courses = forms.ModelMultipleChoiceField(
        queryset=Course.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'select2'}),
        required=False  # Make not required to bypass validation issue
    )
    students = forms.ModelMultipleChoiceField(
        queryset=Student.objects.none(),
        widget=forms.SelectMultiple(attrs={'class': 'select2'}),
        required=True
    )

    class Meta:
        model = Interview
        fields = ['applying_role', 'courses', 'students', 'interview_round','venue', 'location', 'other_location', 'interview_date', 'interview_time']
        widgets = {
            'interview_date': forms.DateInput(attrs={'type': 'date'}),
            'interview_time': forms.TimeInput(attrs={'type': 'time', 'class':'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        parent_interview = kwargs.pop('parent_interview', None)
        super().__init__(*args, **kwargs)
        
        if parent_interview:
            self.fields['applying_role'].initial = parent_interview.applying_role
            self.fields['applying_role'].widget.attrs['readonly'] = True
            
            # Hide the courses field for subsequent rounds
            self.fields['courses'].widget = forms.MultipleHiddenInput()
            self.fields['courses'].queryset = parent_interview.courses.all()
            self.fields['courses'].initial = parent_interview.courses.all()

            # Populate students from the selected ones in the previous round
            selected_students_qs = Student.objects.filter(
                id__in=parent_interview.student_status.filter(status='selected').values_list('student_id', flat=True)
            )
            self.fields['students'].queryset = selected_students_qs
        
        if self.is_bound:
            course_ids = self.data.getlist('courses')
            if course_ids:
                self.fields['students'].queryset = Student.objects.filter(course_id__in=course_ids)
        elif self.instance.pk:
            self.fields['students'].queryset = self.instance.students.all()


class InterviewStudentForm(forms.ModelForm):
    class Meta:
        model = InterviewStudent
        fields = ['status', 'reason', 'offer_letter']

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get("status")
        reason = cleaned_data.get("reason")
        offer_letter = cleaned_data.get("offer_letter")

        if status == 'rejected' and not reason:
            self.add_error('reason', 'This field is required when the status is Rejected.')
            
        if status == 'not_attended' and not reason:
            self.add_error('reason', 'This field is required when the status is Not Attended.')

        if status == 'placed' and not offer_letter:
            self.add_error('offer_letter', 'An offer letter is required when the status is Placed.')

        return cleaned_data
class CompanyFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label='Search',
        widget=forms.TextInput(attrs={'placeholder': 'Search by name, SPOC, etc.'})
    )
    progress = forms.ChoiceField(
        choices=[('', 'All Progress')] + Company.PROGRESS_CHOICES,
        required=False,
        label="Progress"
    )
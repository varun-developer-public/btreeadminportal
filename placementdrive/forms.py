from django import forms
from .models import Company, Interview, InterviewStudent, ResumeSharedStatus
from coursedb.models import Course
from studentsdb.models import Student
from accounts.models import CustomUser as User

class CompanyForm(forms.ModelForm):
    reason_for_not_conducting = forms.CharField(widget=forms.Textarea, required=False)
    
    def clean_mobile(self):
        mobile = self.cleaned_data['mobile']
        if Company.objects.filter(mobile=mobile).exclude(pk=self.instance.pk).exists():
            raise forms.ValidationError("This phone number is already registered.")
        return mobile

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        
        if email and '@' in email:
            domain = email.split('@')[1].lower()
            if Company.objects.filter(email__iendswith=f'@{domain}').exclude(pk=self.instance.pk).exists():
                self.add_error('email', 'This domain is already registered')
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

class ResumeSharedStatusForm(forms.ModelForm):
    courses = forms.ModelMultipleChoiceField(
        queryset=Course.objects.all(),
        widget=forms.SelectMultiple(attrs={'class': 'form-control select2'}),
        required=True
    )
    
    class Meta:
        model = ResumeSharedStatus
        fields = ['status', 'role', 'resumes_shared', 'courses']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['courses'].queryset = Course.objects.all()

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
        
        else:
            # For new interviews, populate with all courses
            self.fields['courses'].queryset = Course.objects.all()

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
class InterviewFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label='Search',
        widget=forms.TextInput(attrs={'placeholder': 'Search by company or role'})
    )
    interview_round = forms.ChoiceField(
        choices=[('', 'All Rounds')] + Interview.ROUND_CHOICES,
        required=False,
        label='Round'
    )
    venue = forms.ChoiceField(
        choices=[('', 'All Venues')] + Interview.VENUE_CHOICES,
        required=False,
        label='Venue'
    )
    location = forms.ChoiceField(
        choices=[('', 'All Locations')] + Interview.LOCATION_CHOICES,
        required=False,
        label='Location'
    )
    courses = forms.ModelMultipleChoiceField(
        queryset=Course.objects.all(),
        required=False,
        label='Courses',
        widget=forms.SelectMultiple(attrs={'class': 'select2'})
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Start Date'
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='End Date'
    )
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
    resume_shared_status = forms.ChoiceField(
        choices=[('', 'All Statuses'), ('none', 'No Status')] + ResumeSharedStatus.STATUS_CHOICES,
        required=False,
        label="Resume Shared"
    )
    company_stack = forms.MultipleChoiceField(
        choices=[],
        label='Stack',
        required=False,
        widget=forms.SelectMultiple(attrs={'class': 'select2', 'data-placeholder': 'Select stack'})
    )
    domain = forms.CharField(
        required=False,
        label='Domain',
        widget=forms.TextInput(attrs={'placeholder': 'Search by domain'})
    )
    location = forms.ChoiceField(
        required=False,
        label='Location',
        choices=[]
    )
    created_by = forms.ModelChoiceField(
        queryset=User.objects.none(),
        required=False,
        label='Created By'
    )
    created_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Created From'
    )
    created_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Created To'
    )
    updated_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Updated From'
    )
    updated_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Updated To'
    )
    interview_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Interview From'
    )
    interview_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label='Interview To'
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        location_choices = [('', 'All Locations')] + [(loc, loc) for loc in Company.objects.values_list('location', flat=True).distinct().order_by('location')]
        self.fields['location'].choices = location_choices

        # Get all course names
        course_choices = [(course.id, course.course_name) for course in Course.objects.all()]
        
        # Get all unique roles from resume shared statuses
        roles = ResumeSharedStatus.objects.exclude(role__isnull=True).exclude(role='').values_list('role', flat=True).distinct()
        role_choices = [(role, f"Role: {role}") for role in roles]
        
        # Combine course and role choices
        self.fields['company_stack'].choices = course_choices + role_choices

        user_ids = Company.objects.values_list('created_by', flat=True).distinct()
        self.fields['created_by'].queryset = User.objects.filter(id__in=user_ids).distinct()
        self.fields['created_by'].label_from_instance = lambda obj: obj.name
        self.fields['created_by'].empty_label = 'All Creators'

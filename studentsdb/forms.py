from django import forms
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from studentsdb.models import Student
from consultantdb.models import Consultant
from settingsdb.models import SourceOfJoining, PaymentAccount

from coursedb.models import CourseCategory, Course
from django_select2.forms import Select2Widget
from core.utils import get_country_code_choices

class StudentForm(forms.ModelForm):
    source_of_joining = forms.ModelChoiceField(
        queryset=SourceOfJoining.objects.all(),
        required=False,
        empty_label="Select Source of Joining"
    )
    consultant = forms.ModelChoiceField(
        queryset=Consultant.objects.all(),
        required=True,
        empty_label="Select Consultant"
    )
    payment_account = forms.ModelChoiceField(
        queryset=PaymentAccount.objects.all(),
        required=True,
        empty_label="Select Payment Account"
    )
    course_category = forms.ModelChoiceField(
        queryset=CourseCategory.objects.all(),
        required=False,
        empty_label="Select Course Category"
    )

    course = forms.ModelChoiceField(
        queryset=Course.objects.none(),  # Start with an empty queryset
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    country_code = forms.CharField(widget=forms.HiddenInput())
    alternative_country_code = forms.CharField(widget=forms.HiddenInput())
    class Meta:
        model = Student
        fields = [
            'first_name', 'last_name', 'country_code', 'phone', 'alternative_country_code', 'alternative_phone', 'email', 'location',
            'ugdegree', 'ugbranch', 'ugpassout', 'ugpercentage',
            'pgdegree', 'pgbranch', 'pgpassout', 'pgpercentage',
            'working_status', 'it_experience',
            'start_date', 'end_date',
            'pl_required', 'source_of_joining',
            'mode_of_class', 'week_type', 'consultant', 'payment_account'
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        # Pop the request object before calling super()
        request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
        today = timezone.now().date()
        self.fields['start_date'].initial = today
        self.fields['end_date'].initial = today + relativedelta(months=4)

        # Set default country code
        if not self.instance.pk:
            self.fields['country_code'].initial = 'IN'
            self.fields['alternative_country_code'].initial = '+91'

        self.fields['course'].queryset = Course.objects.none()

        if 'course_category' in self.data:
            try:
                category_id = int(self.data.get('course_category'))
                self.fields['course'].queryset = Course.objects.filter(category_id=category_id).order_by('course_name')
            except (ValueError, TypeError):
                pass  # invalid input from the client; ignore and fallback to empty queryset
        elif self.instance.pk and self.instance.course_id:
            try:
                course = Course.objects.get(pk=self.instance.course_id)
                self.fields['course_category'].initial = course.category
                self.fields['course'].queryset = Course.objects.filter(category=course.category).order_by('course_name')
                self.fields['course'].initial = course
            except Course.DoesNotExist:
                pass

        # Filter consultants based on user role
        if request:
            user = request.user
            # If the user is a consultant, restrict the list to their own profile
            if hasattr(user, 'consultant_profile'):
                try:
                    consultant = user.consultant_profile.consultant
                    self.fields['consultant'].queryset = Consultant.objects.filter(pk=consultant.pk)
                    self.fields['consultant'].initial = consultant
                    self.fields['consultant'].widget.attrs['readonly'] = True
                except (Consultant.DoesNotExist, AttributeError):
                    # This case might happen if the profile is not set up correctly
                    self.fields['consultant'].queryset = Consultant.objects.none()
            # For staff and superusers, they should see all consultants
            elif user.is_staff or user.is_superuser:
                self.fields['consultant'].queryset = Consultant.objects.all()
            # For any other case, hide the field
            else:
                self.fields['consultant'].queryset = Consultant.objects.none()

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if not first_name.isalpha():
            raise forms.ValidationError("First name should only contain alphabetic characters.")
        return first_name.capitalize()

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if last_name and not last_name.isalpha():
            raise forms.ValidationError("Last name should only contain alphabetic characters.")
        return last_name.capitalize() if last_name else last_name


class StudentUpdateForm(forms.ModelForm):
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

    course_category = forms.ModelChoiceField(
        queryset=CourseCategory.objects.all(),
        required=False,
        empty_label="Select Course Category"
    )

    course = forms.ModelChoiceField(
        queryset=Course.objects.none(),  # Start with an empty queryset
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    country_code = forms.CharField(widget=forms.HiddenInput())
    alternative_country_code = forms.CharField(widget=forms.HiddenInput())
    class Meta:
        model = Student
        fields = [
            'first_name', 'last_name', 'country_code', 'phone', 'alternative_country_code', 'alternative_phone', 'email', 'location',
            'ugdegree', 'ugbranch', 'ugpassout', 'ugpercentage',
            'pgdegree', 'pgbranch', 'pgpassout', 'pgpercentage',
            'working_status', 'it_experience', 'course_status', 'course_percentage',
            'start_date', 'end_date',
            'pl_required', 'source_of_joining',
            'mode_of_class', 'week_type', 'consultant',
            'certificate_issued',
        ]
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'certificate_issued': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)

        # Dynamic course loading based on category
        self.fields['course'].queryset = Course.objects.none()
        if 'course_category' in self.data:
            try:
                category_id = int(self.data.get('course_category'))
                self.fields['course'].queryset = Course.objects.filter(category_id=category_id).order_by('course_name')
            except (ValueError, TypeError):
                pass
        elif self.instance.pk and self.instance.course_id:
            try:
                course = Course.objects.get(pk=self.instance.course_id)
                self.fields['course_category'].initial = course.category
                self.fields['course'].queryset = Course.objects.filter(category=course.category).order_by('course_name')
                self.fields['course'].initial = course
            except Course.DoesNotExist:
                pass


        if user and user.role == 'placement':
            allowed_fields = [
                'ugdegree', 'ugbranch', 'ugpassout', 'ugpercentage',
                'pgdegree', 'pgbranch', 'pgpassout', 'pgpercentage',
                'pl_required', 'course_status', 'course_percentage', 'last_name', 'location', 'alternative_phone',
                'certificate_issued',
            ]
            for field_name, field in self.fields.items():
                if field_name not in allowed_fields:
                    field.disabled = True

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data



class StudentFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label='Search',
        widget=forms.TextInput(attrs={'placeholder': 'Search by name, email, phone, or Student ID'})
    )
    course_category = forms.ModelChoiceField(
        queryset=CourseCategory.objects.all(),
        required=False,
        empty_label="All Categories"
    )
    course = forms.ModelChoiceField(
        queryset=Course.objects.all(),
        required=False,
        empty_label="All Courses"
    )
    course_status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + Student.COURSE_STATUS_CHOICES,
        required=False,
        label="Course Status"
    )
    start_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Enrollment Start Date"
    )
    end_date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={'type': 'date'}),
        label="Enrollment End Date"
    )
    status = forms.ChoiceField(
        choices=[
            ('', 'All'),
            ('mock_interview_completed', 'Mock Interview Completed'),
            ('placement_session_completed', 'Placement Session Completed'),
            ('certificate_issued', 'Certificate Issued'),
            ('onboardingcalldone', 'Onboarding Call Done'),
            ('interviewquestion_shared', 'Interview Question Shared'),
            ('resume_template_shared', 'Resume Template Shared'),
        ],
        required=False,
        label="Status"
    )
class StudentPlacementForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'mock_interview_completed',
            'placement_session_completed',
            'onboardingcalldone',
            'interviewquestion_shared',
            'resume_template_shared',
        ]
        widgets = {
            'mock_interview_completed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'placement_session_completed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'onboardingcalldone': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'interviewquestion_shared': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'resume_template_shared': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

from django import forms
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from studentsdb.models import Student
from consultantdb.models import Consultant
from settingsdb.models import SourceOfJoining

from .models import CourseCategory

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
    course_category = forms.ModelChoiceField(
        queryset=CourseCategory.objects.all(),
        required=False,
        empty_label="Select Course Category"
    )

    class Meta:
        model = Student
        fields = [
            'first_name', 'last_name', 'phone', 'alternative_phone', 'email', 'location',
            'ugdegree', 'ugbranch', 'ugpassout', 'ugpercentage',
            'pgdegree', 'pgbranch', 'pgpassout', 'pgpercentage',
            'working_status', 'it_experience', 'course_category', 'course',
            'start_date', 'end_date',
            'pl_required', 'source_of_joining',
            'mode_of_class', 'week_type', 'consultant'
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
        self.fields['course'].queryset = Course.objects.none()

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


class StudentUpdateForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'first_name', 'last_name', 'phone', 'alternative_phone', 'email', 'location',
            'ugdegree', 'ugbranch', 'ugpassout', 'ugpercentage',
            'pgdegree', 'pgbranch', 'pgpassout', 'pgpercentage',
            'working_status', 'course_status', 'course',
            'end_date',
            'course_percentage',
            'pl_required',
            'mode_of_class',
            'week_type','consultant', 'source_of_joining'
        ]
        widgets = {
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data


from .models import Course

class StudentFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label='Search',
        widget=forms.TextInput(attrs={'placeholder': 'Search by name, email or phone'})
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
    working_status = forms.ChoiceField(
        choices=[('', 'All')] + Student.WORKING_STATUS_CHOICES,
        required=False,
        label="Working Status"
    )

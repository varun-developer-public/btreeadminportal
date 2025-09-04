from django import forms
from studentsdb.models import Student
from coursedb.models import Course, CourseCategory
from .models import Placement, CompanyInterview
from placementdrive.models import Company

class PlacementUpdateForm(forms.ModelForm):
    class Meta:
        model = Placement
        fields = [
            'resume_link',
            'is_active',
            'reason_for_inactive',
            'mock_interview_completed',
            'placement_session_completed',
            'certificate_issued',
        ]
        widgets = {
            'resume_link': forms.FileInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'reason_for_inactive': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'mock_interview_completed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'placement_session_completed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'certificate_issued': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class CompanyInterviewForm(forms.ModelForm):
    class Meta:
        model = CompanyInterview
        fields = ['company', 'applying_for', 'location', 'other_location', 'interview_date', 'interview_time', 'attended', 'feedback']
        widgets = {
            'company': forms.Select(attrs={'class': 'form-control'}),
            'applying_for': forms.TextInput(attrs={'class': 'form-control'}),
            'location': forms.Select(attrs={'class': 'form-control'}),
            'other_location': forms.TextInput(attrs={'class': 'form-control'}),
            'interview_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'interview_time': forms.TimeInput(attrs={'class': 'form-control', 'type': 'time'}),
            'attended': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'feedback': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['company'].queryset = Company.objects.all()

class PlacementFilterForm(forms.Form):
    q = forms.CharField(
        required=False,
        label='Search',
        widget=forms.TextInput(attrs={'placeholder': 'Search by name, email or phone'})
    )
    ug_degree = forms.ChoiceField(required=False, label='UG Degree')
    ug_branch = forms.ChoiceField(required=False, label='UG Branch')
    ug_passout = forms.ChoiceField(required=False, label='UG Passout Year')
    pg_degree = forms.ChoiceField(required=False, label='PG Degree')
    pg_branch = forms.ChoiceField(required=False, label='PG Branch')
    pg_passout = forms.ChoiceField(required=False, label='PG Passout Year')
    batch_id = forms.CharField(required=False, label='Batch ID')
    course_category = forms.ModelChoiceField(
        queryset=CourseCategory.objects.all(),
        required=False,
        empty_label="All Categories",
        label="Course Category"
    )
    course = forms.ModelChoiceField(
        queryset=Course.objects.all(),
        required=False,
        empty_label="All Courses",
        label="Course"
    )
    course_status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + Student.COURSE_STATUS_CHOICES,
        required=False,
        label="Course Status"
    )
    location = forms.CharField(required=False, label='Location')
    course_percentage = forms.IntegerField(required=False, label='Course Percentage')
    resume_status = forms.ChoiceField(
        choices=[('', 'All Resumes'), ('yes', 'Resume Uploaded'), ('no', 'Resume Not Uploaded')],
        required=False,
        label="Resume Status"
    )
    is_active = forms.ChoiceField(
        choices=[('', 'All'), ('yes', 'Active'), ('no', 'Inactive')],
        required=False,
        label="Status"
    )
    interview_count = forms.IntegerField(required=False, label='Interview Count')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ug_degree'].choices = [('', 'All Degrees')] + [(d, d) for d in Student.objects.values_list('ugdegree', flat=True).distinct().order_by('ugdegree') if d]
        self.fields['ug_branch'].choices = [('', 'All Branches')] + [(b, b) for b in Student.objects.values_list('ugbranch', flat=True).distinct().order_by('ugbranch') if b]
        self.fields['ug_passout'].choices = [('', 'All Years')] + [(y, y) for y in Student.objects.values_list('ugpassout', flat=True).distinct().order_by('-ugpassout') if y]
        self.fields['pg_degree'].choices = [('', 'All Degrees')] + [(d, d) for d in Student.objects.values_list('pgdegree', flat=True).distinct().order_by('pgdegree') if d]
        self.fields['pg_branch'].choices = [('', 'All Branches')] + [(b, b) for b in Student.objects.values_list('pgbranch', flat=True).distinct().order_by('pgbranch') if b]
        self.fields['pg_passout'].choices = [('', 'All Years')] + [(y, y) for y in Student.objects.values_list('pgpassout', flat=True).distinct().order_by('-pgpassout') if y]

        self.fields['course_category'].queryset = CourseCategory.objects.all()
        self.fields['course'].queryset = Course.objects.none()

        if 'course_category' in self.data:
            try:
                category_id = int(self.data.get('course_category'))
                self.fields['course'].queryset = Course.objects.filter(category_id=category_id).order_by('course_name')
            except (ValueError, TypeError):
                pass

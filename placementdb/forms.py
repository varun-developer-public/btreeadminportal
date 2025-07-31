from django import forms
from studentsdb.models import Student, Course, CourseCategory
from .models import Placement, CompanyInterview

class PlacementUpdateForm(forms.ModelForm):
    class Meta:
        model = Placement
        fields = [
            'resume_link',
            'is_active',
        ]
        widgets = {
            'resume_link': forms.FileInput(attrs={'class': 'form-control'}),
        }

class CompanyInterviewForm(forms.ModelForm):
    class Meta:
        model = CompanyInterview
        fields = ['company', 'applying_for', 'interview_date', 'interview_time', 'attended']
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['company'].required = False
        widgets = {
            'interview_date': forms.DateInput(attrs={'type': 'date'}),
            'interview_time': forms.TimeInput(attrs={'type': 'time'}),
        }

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['ug_degree'].choices = [('', 'All Degrees')] + [(d, d) for d in Student.objects.values_list('ugdegree', flat=True).distinct().order_by('ugdegree') if d]
        self.fields['ug_branch'].choices = [('', 'All Branches')] + [(b, b) for b in Student.objects.values_list('ugbranch', flat=True).distinct().order_by('ugbranch') if b]
        self.fields['ug_passout'].choices = [('', 'All Years')] + [(y, y) for y in Student.objects.values_list('ugpassout', flat=True).distinct().order_by('-ugpassout') if y]
        self.fields['pg_degree'].choices = [('', 'All Degrees')] + [(d, d) for d in Student.objects.values_list('pgdegree', flat=True).distinct().order_by('pgdegree') if d]
        self.fields['pg_branch'].choices = [('', 'All Branches')] + [(b, b) for b in Student.objects.values_list('pgbranch', flat=True).distinct().order_by('pgbranch') if b]
        self.fields['pg_passout'].choices = [('', 'All Years')] + [(y, y) for y in Student.objects.values_list('pgpassout', flat=True).distinct().order_by('-pgpassout') if y]

        courses = Course.objects.select_related('category').all()
        self.fields['course'].choices = [('', 'All Courses')] + [
            (course.id, f"{course.category.name} - {course.name}") for course in courses
        ]

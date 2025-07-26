from django import forms
from .models import CourseCategory, Course, CourseModule, Topic

class CourseCategoryForm(forms.ModelForm):
    class Meta:
        model = CourseCategory
        fields = ['name', 'code']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
        }

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['course_name', 'code', 'course_type', 'category', 'total_duration']
        widgets = {
            'course_name': forms.TextInput(attrs={'class': 'form-control'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'readonly': 'readonly'}),
            'course_type': forms.Select(attrs={'class': 'form-control'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'total_duration': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        total_duration = cleaned_data.get('total_duration')
        if total_duration and total_duration <= 0:
            raise forms.ValidationError("Total duration must be a positive number.")
        return cleaned_data

class BaseCourseModuleFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()
        total_duration = self.instance.total_duration
        module_durations = 0
        for form in self.forms:
            if not form.cleaned_data or form.cleaned_data.get('DELETE'):
                continue
            module_durations += form.cleaned_data.get('module_duration', 0)
        
        if total_duration != module_durations:
            raise forms.ValidationError(f"The sum of module durations ({module_durations} hours) must equal the total course duration ({total_duration} hours).")

CourseModuleFormSet = forms.inlineformset_factory(
    Course,
    CourseModule,
    fields=('name', 'module_duration', 'has_topics'),
    formset=BaseCourseModuleFormSet,
    extra=1,
    can_delete=True,
    widgets={
        'name': forms.TextInput(attrs={'class': 'form-control'}),
        'module_duration': forms.NumberInput(attrs={'class': 'form-control'}),
        'has_topics': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
    }
)

class BaseTopicFormSet(forms.BaseInlineFormSet):
    def clean(self):
        super().clean()

        # self.instance is the CourseModule instance. It might be unsaved.
        if not hasattr(self.instance, 'has_topics') or not self.instance.has_topics:
            return

        topic_durations = sum(
            form.cleaned_data.get('topic_duration', 0)
            for form in self.forms
            if form.cleaned_data and not form.cleaned_data.get('DELETE')
        )

        module_duration = self.instance.module_duration or 0

        if module_duration != topic_durations:
            # This will be a non-form error on the topic formset
            raise forms.ValidationError(
                f"The sum of topic durations ({topic_durations} hours) "
                f"must equal the module duration ({module_duration} hours)."
            )


TopicFormSet = forms.inlineformset_factory(
    CourseModule,
    Topic,
    fields=('name', 'topic_duration'),
    formset=BaseTopicFormSet,
    extra=1,
    can_delete=True,
    widgets={
        'name': forms.TextInput(attrs={'class': 'form-control'}),
        'topic_duration': forms.NumberInput(attrs={'class': 'form-control'}),
    }
)
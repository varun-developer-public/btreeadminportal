from django import forms
from .models import Student
from django.utils import timezone
from dateutil.relativedelta import relativedelta

class StudentForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'name', 'phone', 'email',
            'join_date','start_date', 'tentative_end_date',
            'course_percentage', 'pl_required', 'source_of_joining',
            'mode_of_class', 'week_type', 'consultant', 'payment_account',
            'total_fees', 'gst_bill', 'amount_paid', 'emi_type',
            'emi_1_amount', 'emi_1_date',
            'emi_2_amount', 'emi_2_date',
            'emi_3_amount', 'emi_3_date',
            'emi_4_amount', 'emi_4_date'
        ]
        widgets = {
            'join_date': forms.DateInput(attrs={
                'type': 'date',
                'readonly': 'readonly'
            }),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'tentative_end_date': forms.DateInput(attrs={'type': 'date'}),
            'emi_1_date': forms.DateInput(attrs={'type': 'date'}),
            'emi_2_date': forms.DateInput(attrs={'type': 'date'}),
            'emi_3_date': forms.DateInput(attrs={'type': 'date'}),
            'emi_4_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = timezone.now().date()
        self.fields['join_date'].initial = today
        self.fields['start_date'].initial = today
        self.fields['tentative_end_date'].initial = today + relativedelta(months=4)

    def clean(self):
        cleaned_data = super().clean()
        emi_type = cleaned_data.get('emi_type')
        total_fees = cleaned_data.get('total_fees') or 0
        amount_paid = cleaned_data.get('amount_paid') or 0

        # Auto-calculate pending amount
        cleaned_data['total_pending_amount'] = total_fees - amount_paid

        # EMI field validation
        if emi_type == '1' and not cleaned_data.get('emi_1_amount'):
            self.add_error('emi_1_amount', 'Please enter EMI 1 amount')
        if emi_type == '2' and not cleaned_data.get('emi_2_amount'):
            self.add_error('emi_2_amount', 'Please enter EMI 2 amount')
        if emi_type == '3' and not cleaned_data.get('emi_3_amount'):
            self.add_error('emi_3_amount', 'Please enter EMI 3 amount')
        if emi_type == '4' and not cleaned_data.get('emi_4_amount'):
            self.add_error('emi_4_amount', 'Please enter EMI 4 amount')

        return cleaned_data

class StudentUpdateForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'name',
            'phone',
            'email',
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
        # (Future) Add PDB sync logic here
        return cleaned_data

from django import forms
from .models import Student
from consultantdb.models import Consultant
from settingsdb.models import SourceOfJoining, PaymentAccount
from django.utils import timezone
from dateutil.relativedelta import relativedelta

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
    payment_account = forms.ModelChoiceField(
        queryset=PaymentAccount.objects.all(),
        required=False,
        empty_label="Select Payment Account"
    )

    class Meta:
        model = Student
        fields = [
            'name', 'phone', 'alternative_phone', 'email',
            'join_date', 'start_date', 'tentative_end_date',
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

        pending = total_fees - amount_paid
        cleaned_data['total_pending_amount'] = pending

        # Collect EMI amounts based on emi_type
        emi_amounts = []
        if emi_type == '2':
            emi_amounts = [
                cleaned_data.get('emi_1_amount') or 0,
                cleaned_data.get('emi_2_amount') or 0
            ]
        elif emi_type == '3':
            emi_amounts = [
                cleaned_data.get('emi_1_amount') or 0,
                cleaned_data.get('emi_2_amount') or 0,
                cleaned_data.get('emi_3_amount') or 0
            ]
        elif emi_type == '4':
            emi_amounts = [
                cleaned_data.get('emi_1_amount') or 0,
                cleaned_data.get('emi_2_amount') or 0,
                cleaned_data.get('emi_3_amount') or 0,
                cleaned_data.get('emi_4_amount') or 0
            ]

        if emi_type in ['2', '3', '4']:
            emi_sum = sum(emi_amounts)
            if emi_sum != pending:
                self.add_error(None, f"Sum of EMI amounts ({emi_sum}) must equal pending amount ({pending})")

        return cleaned_data


class StudentUpdateForm(forms.ModelForm):
    class Meta:
        model = Student
        fields = [
            'name',
            'phone',
            'alternative_phone',
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
        return cleaned_data

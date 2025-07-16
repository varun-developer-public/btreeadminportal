from django import forms
from .models import Payment
from settingsdb.models import PaymentAccount
from dateutil.relativedelta import relativedelta
from django.utils import timezone

class PaymentForm(forms.ModelForm):
    payment_account = forms.ModelChoiceField(
        queryset=PaymentAccount.objects.all(),
        required=False,
        empty_label="Select Payment Account"
    )

    initial_payment_proof = forms.ImageField(required=False)

    class Meta:
        model = Payment
        fields = [
            'payment_account',
            'total_fees', 'gst_bill', 'amount_paid','initial_payment_proof',
            'emi_type',
            'emi_1_amount', 'emi_1_date',
            'emi_2_amount', 'emi_2_date',
            'emi_3_amount', 'emi_3_date',
            'emi_4_amount', 'emi_4_date',
        ]
        widgets = {
            'emi_1_date': forms.DateInput(attrs={'type': 'date'}),
            'emi_2_date': forms.DateInput(attrs={'type': 'date'}),
            'emi_3_date': forms.DateInput(attrs={'type': 'date'}),
            'emi_4_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        today = timezone.now().date()
        self.fields['emi_1_date'].initial = today + relativedelta(months=1)
        self.fields['emi_2_date'].initial = today + relativedelta(months=2)
        self.fields['emi_3_date'].initial = today + relativedelta(months=3)
        self.fields['emi_4_date'].initial = today + relativedelta(months=4)

    def clean(self):
        cleaned_data = super().clean()
        emi_type = cleaned_data.get('emi_type')
        total_fees = cleaned_data.get('total_fees') or 0
        amount_paid = cleaned_data.get('amount_paid') or 0

        pending = total_fees - amount_paid
        cleaned_data['total_pending_amount'] = pending

        if pending > 0 and emi_type == 'NONE':
            self.add_error('emi_type', "Select an EMI option (2/3/4) if there's a pending amount.")

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

from django.core.exceptions import ValidationError

class PaymentUpdateForm(forms.ModelForm):
    emi_1_paid = forms.DecimalField(required=False, max_digits=10, decimal_places=2)
    emi_2_paid = forms.DecimalField(required=False, max_digits=10, decimal_places=2)
    emi_3_paid = forms.DecimalField(required=False, max_digits=10, decimal_places=2)
    emi_4_paid = forms.DecimalField(required=False, max_digits=10, decimal_places=2)

    class Meta:
        model = Payment
        fields = [
            'emi_1_amount', 'emi_1_date', 'emi_1_proof',
            'emi_2_amount', 'emi_2_date', 'emi_2_proof',
            'emi_3_amount', 'emi_3_date', 'emi_3_proof',
            'emi_4_amount', 'emi_4_date', 'emi_4_proof',
        ]
        widgets = {
            'emi_1_date': forms.DateInput(attrs={'type': 'date'}),
            'emi_2_date': forms.DateInput(attrs={'type': 'date'}),
            'emi_3_date': forms.DateInput(attrs={'type': 'date'}),
            'emi_4_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        payment = self.instance

        # Disable EMI fields if proof already uploaded
        for i in range(1, 5):
            if getattr(payment, f"emi_{i}_proof"):
                self.fields[f"emi_{i}_amount"].disabled = True
                self.fields[f"emi_{i}_date"].disabled = True
                self.fields[f"emi_{i}_proof"].disabled = True
                self.fields[f"emi_{i}_paid"].disabled = True

    def clean(self):
        cleaned_data = super().clean()

        for i in range(1, 5):
            amount = cleaned_data.get(f'emi_{i}_amount') or 0
            paid = cleaned_data.get(f'emi_{i}_paid') or 0

            if paid > amount:
                self.add_error(
                    f'emi_{i}_paid',
                    ValidationError(f"Paid amount cannot exceed the EMI amount ({amount}).")
                )

        return cleaned_data


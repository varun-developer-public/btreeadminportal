from django import forms
from .models import Payment
from settingsdb.models import PaymentAccount
from dateutil.relativedelta import relativedelta
from django.utils import timezone
from django.core.exceptions import ValidationError

class PaymentForm(forms.ModelForm):
    EMI_CHOICES = [
        ('NONE', 'No EMI'),
        ('2', '2 EMIs'),
        ('3', '3 EMIs'),
        ('4', '4 EMIs'),
    ]

    emi_type = forms.ChoiceField(choices=EMI_CHOICES, required=True)
    payment_account = forms.ModelChoiceField(
        queryset=PaymentAccount.objects.all(),
        required=False,
        empty_label="Select Payment Account"
    )

    initial_payment_proof = forms.ImageField(
        required=True,
        error_messages={'required': 'Initial payment proof is mandatory'}
    )

    class Meta:
        model = Payment
        fields = [
            'payment_account',
            'total_fees',
            'gst_bill',
            'amount_paid',
            'initial_payment_proof',
            'emi_type',
            'emi_1_amount', 'emi_1_date',
            'emi_2_amount', 'emi_2_date',
            'emi_3_amount', 'emi_3_date',
            'emi_4_amount', 'emi_4_date',
        ]
        widgets = {
            'total_fees': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
            'amount_paid': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
            'emi_1_amount': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
            'emi_2_amount': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
            'emi_3_amount': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
            'emi_4_amount': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
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
        initial_payment_proof = cleaned_data.get('initial_payment_proof')

        # Validate total fees
        if total_fees <= 0:
            raise ValidationError("Total fees must be greater than 0.")

        # Validate initial payment proof
        if not initial_payment_proof and not self.instance.initial_payment_proof:
            raise ValidationError("Initial payment proof is required.")

        # Validate initial payment amount
        if amount_paid <= 0:
            raise ValidationError("Initial payment amount must be greater than 0.")
        if amount_paid > total_fees:
            raise ValidationError("Initial payment must be less than total fees.")

        # Update pending calculation to use EMI commitments
        pending = total_fees - amount_paid
        if max_emis > 0:
            pending = sum(emi_amounts)  # Should equal total_fees - amount_paid
       
        cleaned_data['total_pending_amount'] = pending

        # Validate EMI selection
        if pending > 0:
            if emi_type == 'NONE':
                self.add_error('emi_type', "Select an EMI option (2/3/4) for the pending amount.")
            elif emi_type not in ['2', '3', '4']:
                self.add_error('emi_type', "Invalid EMI type selected.")

        # Process EMI fields based on selected EMI type
        max_emis = int(emi_type) if emi_type in ['2', '3', '4'] else 0

        # Clear EMI fields not corresponding to selected EMI type
        for i in range(1, 5):
            if i > max_emis:
                cleaned_data[f'emi_{i}_amount'] = None
                cleaned_data[f'emi_{i}_date'] = None

        # Validate EMI amounts and dates if EMI is selected
        if max_emis > 0:
            emi_amounts = []
            emi_dates = []
            running_total = 0

            for i in range(1, max_emis + 1):
                amount = cleaned_data.get(f'emi_{i}_amount')
                date = cleaned_data.get(f'emi_{i}_date')

                # Validate individual EMI amount
                if not amount or amount <= 0:
                    self.add_error(f'emi_{i}_amount', f"EMI {i} amount is required and must be greater than 0")
                else:
                    running_total += amount
                    emi_amounts.append(amount)

                # Validate EMI date
                if not date:
                    self.add_error(f'emi_{i}_date', f"EMI {i} date is required")
                else:
                    if i == 1 and date <= timezone.now().date():
                        self.add_error(f'emi_{i}_date', "First EMI date must be in the future")
                    elif i > 1 and date <= emi_dates[-1]:
                        self.add_error(f'emi_{i}_date', f"EMI {i} date must be after EMI {i-1} date")
                    emi_dates.append(date)

            # Validate total EMI amount matches pending amount
            if running_total != pending:
                self.add_error(None, 
                    f"Total EMI amount (₹{running_total}) must equal pending amount (₹{pending})")

        return cleaned_data

class PaymentUpdateForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = [
            'emi_1_paid_amount', 'emi_1_paid_date', 'emi_1_proof',
            'emi_2_paid_amount', 'emi_2_paid_date', 'emi_2_proof',
            'emi_3_paid_amount', 'emi_3_paid_date', 'emi_3_proof',
            'emi_4_paid_amount', 'emi_4_paid_date', 'emi_4_proof',
        ]
        widgets = {
            'emi_1_paid_amount': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
            'emi_2_paid_amount': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
            'emi_3_paid_amount': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
            'emi_4_paid_amount': forms.NumberInput(attrs={'min': '0', 'step': '0.01'}),
            'emi_1_paid_date': forms.DateInput(attrs={'type': 'date'}),
            'emi_2_paid_date': forms.DateInput(attrs={'type': 'date'}),
            'emi_3_paid_date': forms.DateInput(attrs={'type': 'date'}),
            'emi_4_paid_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        payment = self.instance
        next_emi = payment.get_next_payable_emi()

        # Disable all fields by default
        for field in self.fields:
            self.fields[field].disabled = True
            self.fields[field].required = False
            if 'paid_amount' in field:
                self.fields[field].widget.attrs.update({
                    'class': 'emi-paid-amount',
                    'data-emi': field.split('_')[1]
                })

        # Enable only the current EMI fields if they can be edited
        if next_emi and payment.can_edit_emi(next_emi):
            self.fields[f'emi_{next_emi}_paid_amount'].disabled = False
            self.fields[f'emi_{next_emi}_paid_date'].disabled = False
            self.fields[f'emi_{next_emi}_proof'].disabled = False
            
            # Make enabled fields required
            self.fields[f'emi_{next_emi}_paid_amount'].required = True
            self.fields[f'emi_{next_emi}_paid_date'].required = True

            # Set min/max for paid amount
            original_amount = getattr(payment, f'emi_{next_emi}_amount') or 0
            self.fields[f'emi_{next_emi}_paid_amount'].widget.attrs.update({
                'max': original_amount,
                'data-original': original_amount
            })

    def clean(self):
        cleaned_data = super().clean()
        payment = self.instance
        next_emi = payment.get_next_payable_emi()

        if next_emi and payment.can_edit_emi(next_emi):
            original_amount = getattr(payment, f'emi_{next_emi}_amount') or 0
            paid_amount = cleaned_data.get(f'emi_{next_emi}_paid_amount') or 0
            paid_date = cleaned_data.get(f'emi_{next_emi}_paid_date')
            proof = cleaned_data.get(f'emi_{next_emi}_proof')

            # Validate paid amount
            if paid_amount <= 0:
                self.add_error(f'emi_{next_emi}_paid_amount', "Paid amount must be greater than 0")
            elif paid_amount > original_amount:
                self.add_error(f'emi_{next_emi}_paid_amount', 
                    f"Paid amount (₹{paid_amount}) cannot exceed the EMI amount (₹{original_amount})")

            # Handle carry forward amount without modifying next EMI
            if paid_amount < original_amount:
                carry_forward = original_amount - paid_amount
                next_emi_num = next_emi + 1
                if next_emi_num <= 4 and getattr(payment, f'emi_{next_emi_num}_amount') is not None:
                    self.add_error(None, 
                        f"Note: Remaining ₹{carry_forward} must be paid with EMI {next_emi_num}")
                else:
                    self.add_error(None,
                        f"Note: Remaining ₹{carry_forward} must be paid in the next payment")

            # Validate paid date
            if paid_date:
                today = timezone.now().date()
                if paid_date > today:
                    self.add_error(f'emi_{next_emi}_paid_date', "Paid date cannot be in the future")
                
                emi_due_date = getattr(payment, f'emi_{next_emi}_date')
                if emi_due_date:
                    earliest_allowed = emi_due_date - relativedelta(months=1)
                    if paid_date < earliest_allowed:
                        self.add_error(f'emi_{next_emi}_paid_date', 
                            f"Paid date must be within one month of due date ({emi_due_date.strftime('%d/%m/%Y')})")

            # Validate proof
            if paid_amount > 0 and not proof and not getattr(payment, f'emi_{next_emi}_proof'):
                self.add_error(f'emi_{next_emi}_proof', "Payment proof is required")

        return cleaned_data


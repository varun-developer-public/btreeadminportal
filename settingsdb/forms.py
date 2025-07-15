from django import forms
from .models import SourceOfJoining, PaymentAccount

class SourceForm(forms.ModelForm):
    class Meta:
        model = SourceOfJoining
        fields = ['name']

class PaymentAccountForm(forms.ModelForm):
    class Meta:
        model = PaymentAccount
        fields = ['name']

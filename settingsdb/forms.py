from django import forms
from .models import SourceOfJoining, PaymentAccount, UserSettings

class SourceForm(forms.ModelForm):
    class Meta:
        model = SourceOfJoining
        fields = ['name']

class PaymentAccountForm(forms.ModelForm):
    class Meta:
        model = PaymentAccount
        fields = ['name']

class UserSettingsForm(forms.ModelForm):
    class Meta:
        model = UserSettings
        fields = ['enable_2fa']

from django import forms
from .models import SourceOfJoining, PaymentAccount, UserSettings, DBBackupImport
import os

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


class DBBackupImportForm(forms.ModelForm):
    class Meta:
        model = DBBackupImport
        fields = ['uploaded_file']
        
    def clean_uploaded_file(self):
        uploaded_file = self.cleaned_data.get('uploaded_file')
        if uploaded_file:
            # Check file extension
            ext = os.path.splitext(uploaded_file.name)[1].lower()
            if ext != '.sql':
                raise forms.ValidationError("Only .sql files are allowed.")
            
            # Check file size (limit to 50MB)
            if uploaded_file.size > 50 * 1024 * 1024:  # 50MB in bytes
                raise forms.ValidationError("File size must be under 50MB.")
                
        return uploaded_file

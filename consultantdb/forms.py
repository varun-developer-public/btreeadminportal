from django import forms
from .models import Consultant

class ConsultantForm(forms.ModelForm):
    class Meta:
        model = Consultant
        fields = ['name', 'phone_number', 'email', 'address', 'date_of_birth']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

class ConsultantProfileForm(forms.ModelForm):
    profile_picture = forms.ImageField(required=False, label="Profile Picture")

    class Meta:
        model = Consultant
        fields = ['name', 'phone_number', 'email', 'address', 'date_of_birth']
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and hasattr(self.instance, 'consultantprofile'):
            self.fields['profile_picture'].initial = self.instance.consultantprofile.user.profile_picture

    def save(self, commit=True):
        consultant = super().save(commit)
        
        profile_picture = self.cleaned_data.get('profile_picture')
        if profile_picture is not None:
            user = self.instance.consultantprofile.user
            if profile_picture is False:
                user.profile_picture.delete(save=False)
            else:
                user.profile_picture = profile_picture
            
            if commit:
                user.save()

        return consultant

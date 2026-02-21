from django import forms
from django.forms import inlineformset_factory
from .models import JobCard, JobDetail, CompanyProfile

class JobCardForm(forms.ModelForm):
    class Meta:
        model = JobCard
        fields = ['client_name', 'client_email', 'company_name']
        widgets = {
            'client_name': forms.TextInput(attrs={'class': 'form-control'}),
            'client_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'company_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

class JobDetailForm(forms.ModelForm):
    class Meta:
        model = JobDetail
        fields = ['description', 'hardware_replaced', 'quantity']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Description'}),
            'hardware_replaced': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Hardware Replaced'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
        }

JobDetailFormSet = inlineformset_factory(
    JobCard, JobDetail, form=JobDetailForm,
    extra=1, can_delete=True
)

class SignatureSubmissionForm(forms.Form):
    technician_signature = forms.CharField(widget=forms.HiddenInput())
    client_signature = forms.CharField(widget=forms.HiddenInput())

class ManagerReviewForm(forms.ModelForm):
    manager_signature_data = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = JobCard
        fields = ['start_time', 'end_time', 'manager_notes']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'end_time': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}, format='%Y-%m-%dT%H:%M'),
            'manager_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.start_time:
            self.fields['start_time'].initial = self.instance.start_time.strftime('%Y-%m-%dT%H:%M')
        if self.instance and self.instance.end_time:
            self.fields['end_time'].initial = self.instance.end_time.strftime('%Y-%m-%dT%H:%M')

class CompanyProfileForm(forms.ModelForm):
    extra_fields = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = CompanyProfile
        fields = ['logo', 'address', 'default_email', 'extra_fields']
        widgets = {
            'logo': forms.FileInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'default_email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

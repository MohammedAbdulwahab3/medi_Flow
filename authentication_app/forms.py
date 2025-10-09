from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()

class PatientSignUpForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = User.ROLE_PATIENT
        if commit:
            user.save()
        return user


class AdminUserCreateForm(UserCreationForm):
    role = forms.ChoiceField(choices=[
        (User.ROLE_DOCTOR, 'Doctor'),
        (User.ROLE_PHARMACIST, 'Pharmacist'),
        (User.ROLE_MANUFACTURER, 'Manufacturer'),
    ])
    license_number = forms.CharField(required=False)
    email = forms.EmailField(required=False)

    class Meta:
        model = User
        fields = ['username', 'email', 'role', 'license_number', 'password1', 'password2']

    def save(self, commit=True):
        user = super().save(commit=False)
        user.role = self.cleaned_data['role']
        ln = self.cleaned_data.get('license_number')
        user.license_number = ln or None
        if commit:
            user.save()
        return user

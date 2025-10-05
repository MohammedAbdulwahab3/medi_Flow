from django import forms
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import (
    Prescription, PatientHistoryEntry, DoctorProfile, 
    PatientDoctorAssignment, Message, Notification
)
from inventory.models import PharmacyInventory
from medicine.models import Medicine


User = get_user_model()


class DoctorPrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ['patient', 'medicine', 'dosage', 'duration', 'quantity', 'notes']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-control'}),
            'medicine': forms.Select(attrs={'class': 'form-control'}),
            'dosage': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 1 tablet twice daily'}),
            'duration': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 5 days'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Optional notes'}),
        }

    def __init__(self, doctor_user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Only patients as targets
        self.fields['patient'].queryset = User.objects.filter(role=User.ROLE_PATIENT)
        # Filter medicines to active ones
        self.fields['medicine'].queryset = Medicine.objects.filter(is_active=True)

    def clean(self):
        cleaned_data = super().clean()
        quantity = cleaned_data.get('quantity')
        if quantity is not None and quantity <= 0:
            raise forms.ValidationError('Quantity must be positive')
        return cleaned_data


class PharmacistDispenseForm(forms.ModelForm):
    pharmacy_inventory = forms.ModelChoiceField(
        queryset=PharmacyInventory.objects.none(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = Prescription
        fields = ['status', 'notes']
        widgets = {
            'status': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        pharmacist = kwargs.pop('pharmacist', None)
        prescription = kwargs.get('instance')
        super().__init__(*args, **kwargs)
        # Only allow selecting inventory for the prescription medicine with stock
        if pharmacist and prescription:
            self.fields['pharmacy_inventory'].queryset = PharmacyInventory.objects.filter(
                pharmacist=pharmacist,
                batch__medicine=prescription.medicine,
                current_stock__gt=0
            ).select_related('batch')

    def clean(self):
        cleaned = super().clean()
        status = cleaned.get('status')
        inv = cleaned.get('pharmacy_inventory')
        prescription = self.instance
        if status == 'dispensed':
            if inv is None:
                raise forms.ValidationError('Select a pharmacy stock batch to dispense from.')
            if inv.current_stock < (prescription.quantity or 0):
                raise forms.ValidationError(f'Not enough stock in selected batch. Available: {inv.current_stock}.')
        return cleaned


class DoctorHistoryEntryForm(forms.ModelForm):
    class Meta:
        model = PatientHistoryEntry
        fields = ['case_summary', 'diagnosis', 'treatment_plan', 'notes']
        widgets = {
            'case_summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Chief complaint / case summary'}),
            'diagnosis': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'treatment_plan': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }


class DoctorProfileForm(forms.ModelForm):
    class Meta:
        model = DoctorProfile
        fields = ['specialization', 'qualifications', 'e_signature', 'years_of_experience', 
                  'consultation_fee', 'available_days', 'available_hours']
        widgets = {
            'specialization': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Cardiology'}),
            'qualifications': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'e.g., MD, MBBS, Board Certified'}),
            'e_signature': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Your digital signature'}),
            'years_of_experience': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'consultation_fee': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'available_days': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Mon-Fri'}),
            'available_hours': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 9:00 AM - 5:00 PM'}),
        }


class MessageForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['recipient', 'subject', 'body']
        widgets = {
            'recipient': forms.Select(attrs={'class': 'form-control'}),
            'subject': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Message subject'}),
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Your message'}),
        }

    def __init__(self, sender=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if sender:
            # If sender is a doctor, show their patients
            if sender.is_doctor:
                # Get patients from prescriptions or assignments
                patient_ids = Prescription.objects.filter(doctor=sender).values_list('patient_id', flat=True).distinct()
                assigned_patient_ids = PatientDoctorAssignment.objects.filter(doctor=sender).values_list('patient_id', flat=True).distinct()
                all_patient_ids = set(list(patient_ids) + list(assigned_patient_ids))
                self.fields['recipient'].queryset = User.objects.filter(id__in=all_patient_ids, role=User.ROLE_PATIENT)
            # If sender is a patient, show their doctors
            elif sender.is_patient:
                doctor_ids = Prescription.objects.filter(patient=sender).values_list('doctor_id', flat=True).distinct()
                assigned_doctor_ids = PatientDoctorAssignment.objects.filter(patient=sender).values_list('doctor_id', flat=True).distinct()
                all_doctor_ids = set(list(doctor_ids) + list(assigned_doctor_ids))
                self.fields['recipient'].queryset = User.objects.filter(id__in=all_doctor_ids, role=User.ROLE_DOCTOR)
            else:
                self.fields['recipient'].queryset = User.objects.none()


class MessageReplyForm(forms.ModelForm):
    class Meta:
        model = Message
        fields = ['body']
        widgets = {
            'body': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Your reply'}),
        }


class PatientDoctorAssignmentForm(forms.ModelForm):
    class Meta:
        model = PatientDoctorAssignment
        fields = ['patient', 'doctor', 'is_primary', 'notes']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-control'}),
            'doctor': forms.Select(attrs={'class': 'form-control'}),
            'is_primary': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['patient'].queryset = User.objects.filter(role=User.ROLE_PATIENT)
        self.fields['doctor'].queryset = User.objects.filter(role=User.ROLE_DOCTOR)

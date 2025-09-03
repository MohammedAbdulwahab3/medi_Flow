from django import forms
from django.utils import timezone
from django.contrib.auth import get_user_model
from .models import Prescription, PatientHistoryEntry
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



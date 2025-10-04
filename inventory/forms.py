from django import forms
from .models import Inventory, MedicineTransfer
from medicine.models import MedicineBatch
from authentication_app.models import User

class InventoryForm(forms.ModelForm):
    class Meta:
        model = Inventory
        fields = ['current_stock', 'minimum_stock_level']
        widgets = {
            'current_stock': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
            'minimum_stock_level': forms.NumberInput(attrs={'class': 'form-control', 'min': 0}),
        }


class MedicineTransferForm(forms.ModelForm):
    class Meta:
        model = MedicineTransfer
        fields = ['transfer_type', 'from_user', 'to_user', 'batch', 'quantity', 'notes']
        widgets = {
            'transfer_type': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('', 'Select transfer type'),
                ('manufacturer_to_pharmacy', 'Manufacturer to Pharmacy'),
                ('pharmacy_to_doctor', 'Pharmacy to Doctor'),
                ('doctor_to_patient', 'Doctor to Patient'),
                ('return', 'Return'),
            ]),
            'from_user': forms.Select(attrs={'class': 'form-control'}),
            'to_user': forms.Select(attrs={'class': 'form-control'}),
            'batch': forms.Select(attrs={'class': 'form-control'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Transfer notes (optional)'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        batch = cleaned_data.get('batch')
        quantity = cleaned_data.get('quantity')
        
        if batch and quantity:
            # Check if enough stock is available
            if batch.inventory.current_stock < quantity:
                raise forms.ValidationError(f"Insufficient stock. Only {batch.inventory.current_stock} units available.")
            
            # Check if batch is expired
            if batch.is_expired:
                raise forms.ValidationError("Cannot transfer expired batch.")
        
        return cleaned_data


class ReservationRequestForm(forms.Form):
    manufacturer_id = forms.IntegerField(widget=forms.HiddenInput(), required=True)
    medicine_id = forms.IntegerField(widget=forms.HiddenInput(), required=True)
    quantity = forms.IntegerField(min_value=1, widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1}))
    note = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2}))

    def clean_manufacturer_id(self):
        mid = self.cleaned_data.get('manufacturer_id')
        from authentication_app.models import User
        try:
            m = User.objects.get(id=mid, role=User.ROLE_MANUFACTURER)
        except User.DoesNotExist:
            raise forms.ValidationError('Selected manufacturer not found')
        return mid

    def clean_medicine_id(self):
        mid = self.cleaned_data.get('medicine_id')
        from medicine.models import Medicine
        try:
            Medicine.objects.get(id=mid)
        except Medicine.DoesNotExist:
            raise forms.ValidationError('Selected medicine not found')
        return mid

from django import forms
from .models import Inventory, MedicineTransfer, Sale, SaleItem, ReorderAlert
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


class DispensePrescriptionForm(forms.Form):
    """Form for dispensing a prescription"""
    prescription_id = forms.IntegerField(widget=forms.HiddenInput())
    batch_id = forms.IntegerField(required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    quantity = forms.IntegerField(min_value=1, widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 1}))
    payment_method = forms.ChoiceField(
        choices=[
            ('cash', 'Cash'),
            ('card', 'Card'),
            ('mobile', 'Mobile Payment'),
            ('insurance', 'Insurance'),
        ],
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    notes = forms.CharField(required=False, widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Additional notes (optional)'}))
    
    def __init__(self, *args, pharmacist=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.pharmacist = pharmacist
    
    def clean(self):
        cleaned_data = super().clean()
        prescription_id = cleaned_data.get('prescription_id')
        batch_id = cleaned_data.get('batch_id')
        quantity = cleaned_data.get('quantity')
        
        if prescription_id and batch_id and quantity and self.pharmacist:
            from prescription.models import Prescription
            from .models import PharmacyInventory
            
            try:
                prescription = Prescription.objects.get(id=prescription_id)
                if prescription.status != 'pending':
                    raise forms.ValidationError('This prescription has already been processed.')
                
                # Check pharmacy inventory
                inventory = PharmacyInventory.objects.filter(
                    pharmacist=self.pharmacist,
                    batch_id=batch_id
                ).first()
                
                if not inventory or inventory.current_stock < quantity:
                    raise forms.ValidationError('Insufficient stock to dispense this prescription.')
                    
            except Prescription.DoesNotExist:
                raise forms.ValidationError('Prescription not found.')
        
        return cleaned_data


class SaleForm(forms.ModelForm):
    """Form for recording a sale"""
    class Meta:
        model = Sale
        fields = ['patient', 'payment_method', 'notes']
        widgets = {
            'patient': forms.Select(attrs={'class': 'form-control'}),
            'payment_method': forms.Select(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Sale notes (optional)'}),
        }


class ReorderAlertForm(forms.ModelForm):
    """Form for managing reorder alerts"""
    class Meta:
        model = ReorderAlert
        fields = ['suggested_quantity', 'notes']
        widgets = {
            'suggested_quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Notes about reorder (optional)'}),
        }

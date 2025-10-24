from django import forms
from .models import Medicine, MedicineBatch
from datetime import date

class MedicineForm(forms.ModelForm):
    class Meta:
        model = Medicine
        fields = ['name', 'generic_name', 'strength', 'dosage_form', 'category', 'description', 'image']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Paracetamol', 'required': True}),
            'generic_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Acetaminophen'}),
            'strength': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 500mg, 10ml'}),
            'dosage_form': forms.Select(attrs={'class': 'form-control'}, choices=[
                ('', 'Select dosage form'),
                ('tablet', 'Tablet'),
                ('capsule', 'Capsule'),
                ('syrup', 'Syrup'),
                ('injection', 'Injection'),
                ('cream', 'Cream'),
                ('ointment', 'Ointment'),
                ('drops', 'Drops'),
                ('inhaler', 'Inhaler'),
                ('powder', 'Powder'),
                ('suspension', 'Suspension'),
                ('gel', 'Gel'),
                ('spray', 'Spray'),
                ('patch', 'Patch'),
                ('other', 'Other')
            ]),
            'category': forms.Select(attrs={'class': 'form-control', 'required': True}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter medicine description, uses, and precautions...'}),
            'image': forms.URLInput(attrs={'class': 'form-control', 'placeholder': 'https://example.com/medicine-image.jpg (optional)'}),
        }
    
    def clean_name(self):
        name = self.cleaned_data.get('name')
        if name:
            name = name.strip()
            if len(name) < 2:
                raise forms.ValidationError('Medicine name must be at least 2 characters long.')
        return name
    
    def clean_strength(self):
        strength = self.cleaned_data.get('strength')
        if strength:
            strength = strength.strip()
        return strength


class MedicineBatchForm(forms.ModelForm):
    class Meta:
        model = MedicineBatch
        fields = ['medicine', 'batch_number', 'quantity', 'manufacturing_date', 'expiry_date', 'cost_price', 'selling_price']
        widgets = {
            'medicine': forms.Select(attrs={'class': 'form-control', 'required': True}),
            'batch_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., BATCH-001', 'required': True}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'placeholder': 'Number of units', 'required': True}),
            'manufacturing_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'required': True}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date', 'required': True}),
            'cost_price': forms.NumberInput(attrs={'class': 'form-control', 'min': 0.01, 'step': 0.01, 'placeholder': 'Cost per unit', 'required': True}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control', 'min': 0.01, 'step': 0.01, 'placeholder': 'Selling price per unit', 'required': True}),
        }

    def __init__(self, manufacturer_user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if manufacturer_user:
            self.fields['medicine'].queryset = Medicine.objects.filter(manufacturer=manufacturer_user, is_active=True)
            self.fields['medicine'].empty_label = "Select a medicine"
        else:
            self.fields['medicine'].queryset = Medicine.objects.filter(is_active=True)

    def clean_batch_number(self):
        batch_number = self.cleaned_data.get('batch_number')
        if batch_number:
            batch_number = batch_number.strip().upper()
            # Check for duplicate batch numbers
            if self.instance.pk:
                # Editing existing batch
                if MedicineBatch.objects.filter(batch_number=batch_number).exclude(pk=self.instance.pk).exists():
                    raise forms.ValidationError('A batch with this number already exists.')
            else:
                # Creating new batch
                if MedicineBatch.objects.filter(batch_number=batch_number).exists():
                    raise forms.ValidationError('A batch with this number already exists.')
        return batch_number

    def clean(self):
        cleaned_data = super().clean()
        manufacturing_date = cleaned_data.get('manufacturing_date')
        expiry_date = cleaned_data.get('expiry_date')
        cost_price = cleaned_data.get('cost_price')
        selling_price = cleaned_data.get('selling_price')
        
        # Validate dates
        if manufacturing_date and expiry_date:
            if manufacturing_date >= expiry_date:
                raise forms.ValidationError("Expiry date must be after manufacturing date.")
            
            # Check if manufacturing date is not in future
            from datetime import date
            if manufacturing_date > date.today():
                raise forms.ValidationError("Manufacturing date cannot be in the future.")
        
        # Validate pricing
        if cost_price and selling_price:
            if selling_price < cost_price:
                # Warning but don't block (some scenarios might sell at loss)
                self.add_error('selling_price', 'Warning: Selling price is less than cost price. This will result in a loss.')
        
        return cleaned_data

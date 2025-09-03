from django import forms
from .models import Medicine, MedicineBatch

class MedicineForm(forms.ModelForm):
    class Meta:
        model = Medicine
        fields = ['name', 'generic_name', 'strength', 'dosage_form', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Medicine name'}),
            'generic_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Generic name'}),
            'strength': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., 500mg'}),
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
                ('other', 'Other')
            ]),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Description'}),
        }


class MedicineBatchForm(forms.ModelForm):
    class Meta:
        model = MedicineBatch
        fields = ['medicine', 'batch_number', 'quantity', 'manufacturing_date', 'expiry_date', 'cost_price', 'selling_price']
        widgets = {
            'medicine': forms.Select(attrs={'class': 'form-control'}),
            'batch_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Batch number'}),
            'quantity': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'manufacturing_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'expiry_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'cost_price': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': 0.01}),
            'selling_price': forms.NumberInput(attrs={'class': 'form-control', 'min': 0, 'step': 0.01}),
        }

    def __init__(self, manufacturer_user=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if manufacturer_user:
            self.fields['medicine'].queryset = Medicine.objects.filter(manufacturer=manufacturer_user, is_active=True)

    def clean(self):
        cleaned_data = super().clean()
        manufacturing_date = cleaned_data.get('manufacturing_date')
        expiry_date = cleaned_data.get('expiry_date')
        
        if manufacturing_date and expiry_date and manufacturing_date >= expiry_date:
            raise forms.ValidationError("Expiry date must be after manufacturing date")
        
        return cleaned_data

from django.db import models
from django.conf import settings

class Medicine(models.Model):
    CATEGORY_CHOICES = [
        ('pain_relief', 'Pain Relief'),
        ('antibiotics', 'Antibiotics'),
        ('cardiovascular', 'Cardiovascular'),
        ('diabetes', 'Diabetes'),
        ('respiratory', 'Respiratory'),
        ('gastrointestinal', 'Gastrointestinal'),
        ('vitamins', 'Vitamins & Supplements'),
        ('skin_care', 'Skin Care'),
        ('other', 'Other'),
    ]
    
    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200, blank=True, null=True)
    strength = models.CharField(max_length=100, blank=True, null=True)
    dosage_form = models.CharField(max_length=100, blank=True, null=True)  # tablet, syrup, injection, etc.
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, default='other')
    description = models.TextField(blank=True, null=True)
    image = models.URLField(max_length=500, blank=True, null=True, help_text="URL to medicine image")
    manufacturer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'manufacturer'})
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.strength} {self.dosage_form}"
    
    def get_price_range(self):
        """Get min and max selling price from all batches"""
        from django.db.models import Min, Max
        prices = self.batches.filter(is_active=True).aggregate(
            min_price=Min('selling_price'),
            max_price=Max('selling_price')
        )
        return prices

    class Meta:
        ordering = ['name']


class MedicineBatch(models.Model):
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE, related_name='batches')
    batch_number = models.CharField(max_length=100, unique=True)
    quantity = models.PositiveIntegerField()
    manufacturing_date = models.DateField()
    expiry_date = models.DateField()
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    selling_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.medicine.name} - Batch {self.batch_number}"

    @property
    def is_expired(self):
        from django.utils import timezone
        return timezone.now().date() > self.expiry_date

    @property
    def is_expiring_soon(self):
        from django.utils import timezone
        from datetime import timedelta
        warning_date = timezone.now().date() + timedelta(days=30)
        return self.expiry_date <= warning_date

    class Meta:
        ordering = ['-manufacturing_date']

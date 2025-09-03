from django.db import models
from django.conf import settings

class Medicine(models.Model):
    name = models.CharField(max_length=200)
    generic_name = models.CharField(max_length=200, blank=True, null=True)
    strength = models.CharField(max_length=100, blank=True, null=True)
    dosage_form = models.CharField(max_length=100, blank=True, null=True)  # tablet, syrup, injection, etc.
    description = models.TextField(blank=True, null=True)
    manufacturer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'role': 'manufacturer'})
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} - {self.strength} {self.dosage_form}"

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

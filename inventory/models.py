from django.db import models
from django.conf import settings
from medicine.models import MedicineBatch
from authentication_app.models import User

class Inventory(models.Model):
    batch = models.OneToOneField(MedicineBatch, on_delete=models.CASCADE, related_name='inventory')
    current_stock = models.PositiveIntegerField()
    reserved_stock = models.PositiveIntegerField(default=0)
    minimum_stock_level = models.PositiveIntegerField(default=10)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.batch.medicine.name} - Stock: {self.current_stock}"

    @property
    def available_stock(self):
        current = self.current_stock or 0
        reserved = self.reserved_stock or 0
        return current - reserved

    @property
    def needs_restock(self):
        return self.available_stock <= (self.minimum_stock_level or 0)


class MedicineTransfer(models.Model):
    TRANSFER_TYPES = [
        ('manufacturer_to_pharmacy', 'Manufacturer to Pharmacy'),
        ('pharmacy_to_pharmacy', 'Pharmacy to Pharmacy'),
        ('pharmacy_to_patient', 'Pharmacy to Patient'),
    ]
    
    transfer_type = models.CharField(max_length=50, choices=TRANSFER_TYPES)
    from_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transfers_sent')
    to_user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='transfers_received')
    batch = models.ForeignKey(MedicineBatch, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    transfer_date = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True, null=True)
    is_completed = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.batch.medicine.name} - {self.quantity} units to {self.to_user.username}"

    class Meta:
        ordering = ['-transfer_date']


class PharmacyInventory(models.Model):
    pharmacist = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pharmacy_inventory')
    batch = models.ForeignKey(MedicineBatch, on_delete=models.CASCADE)
    current_stock = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('pharmacist', 'batch')

    def __str__(self):
        return f"{self.pharmacist.username} - {self.batch.medicine.name} ({self.current_stock})"

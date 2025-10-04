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


class ReservationRequest(models.Model):
    # Normalize status choices per request: pending, reserved, rejected, transferred
    STATUS_PENDING = 'pending'
    STATUS_RESERVED = 'reserved'
    STATUS_REJECTED = 'rejected'
    STATUS_TRANSFERRED = 'transferred'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_RESERVED, 'Reserved'),
        (STATUS_REJECTED, 'Rejected'),
        (STATUS_TRANSFERRED, 'Transferred'),
    ]

    pharmacy = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reservation_requests')
    manufacturer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='received_reservation_requests')
    medicine = models.ForeignKey('medicine.Medicine', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    responded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='+')
    responded_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Request {self.id}: {self.medicine.name} x{self.quantity} from {self.manufacturer.username} to {self.pharmacy.username} ({self.status})"

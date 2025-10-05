from django.db import models
from django.conf import settings
from medicine.models import MedicineBatch
from authentication_app.models import User

class Warehouse(models.Model):
    """Manufacturer warehouse/location for stock holding."""
    manufacturer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='warehouses', limit_choices_to={'role': 'manufacturer'})
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('manufacturer', 'name')
        ordering = ['manufacturer__username', 'name']

    def __str__(self):
        return f"{self.name} ({self.manufacturer.username})"


class Inventory(models.Model):
    batch = models.OneToOneField(MedicineBatch, on_delete=models.CASCADE, related_name='inventory')
    current_stock = models.PositiveIntegerField()
    reserved_stock = models.PositiveIntegerField(default=0)
    minimum_stock_level = models.PositiveIntegerField(default=10)
    last_updated = models.DateTimeField(auto_now=True)
    warehouse = models.ForeignKey('Warehouse', on_delete=models.SET_NULL, null=True, blank=True, related_name='inventories')

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
    selling_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Pharmacy's selling price (if different from batch price)")
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('pharmacist', 'batch')

    def __str__(self):
        return f"{self.pharmacist.username} - {self.batch.medicine.name} ({self.current_stock})"
    
    def get_price(self):
        """Return pharmacy's price if set, otherwise batch price"""
        return self.selling_price if self.selling_price else self.batch.selling_price


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


class Sale(models.Model):
    """Track pharmacy sales transactions"""
    pharmacist = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pharmacy_sales')
    patient = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='purchases', limit_choices_to={'role': 'patient'})
    prescription = models.ForeignKey('prescription.Prescription', on_delete=models.SET_NULL, null=True, blank=True, related_name='sales')
    sale_date = models.DateTimeField(auto_now_add=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, choices=[
        ('cash', 'Cash'),
        ('card', 'Card'),
        ('mobile', 'Mobile Payment'),
        ('insurance', 'Insurance'),
    ], default='cash')
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-sale_date']
    
    def __str__(self):
        return f"Sale #{self.id} - {self.total_amount} on {self.sale_date:%Y-%m-%d}"
    
    @property
    def profit(self):
        """Calculate profit from sale items"""
        profit = 0
        for item in self.items.all():
            cost = float(item.batch.cost_price or 0) * item.quantity
            revenue = float(item.unit_price) * item.quantity
            profit += revenue - cost
        return profit


class SaleItem(models.Model):
    """Individual items in a sale transaction"""
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name='items')
    batch = models.ForeignKey(MedicineBatch, on_delete=models.CASCADE)
    pharmacy_inventory = models.ForeignKey(PharmacyInventory, on_delete=models.SET_NULL, null=True, blank=True)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.batch.medicine.name} x{self.quantity} @ {self.unit_price}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate subtotal
        self.subtotal = self.quantity * self.unit_price
        super().save(*args, **kwargs)


class ReorderAlert(models.Model):
    """Track reorder alerts for low stock items"""
    STATUS_PENDING = 'pending'
    STATUS_ORDERED = 'ordered'
    STATUS_COMPLETED = 'completed'
    STATUS_DISMISSED = 'dismissed'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_ORDERED, 'Ordered'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_DISMISSED, 'Dismissed'),
    ]
    
    pharmacist = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reorder_alerts')
    pharmacy_inventory = models.ForeignKey(PharmacyInventory, on_delete=models.CASCADE, related_name='reorder_alerts')
    threshold_quantity = models.PositiveIntegerField(help_text="Stock level that triggered this alert")
    suggested_quantity = models.PositiveIntegerField(help_text="Suggested reorder quantity")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reservation_request = models.ForeignKey(ReservationRequest, on_delete=models.SET_NULL, null=True, blank=True, related_name='reorder_alerts')
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Reorder Alert: {self.pharmacy_inventory.batch.medicine.name} - {self.status}"

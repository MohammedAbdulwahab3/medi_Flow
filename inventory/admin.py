from django.contrib import admin
from .models import Inventory, MedicineTransfer, Warehouse

@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    list_display = ['batch', 'current_stock', 'reserved_stock', 'available_stock', 'minimum_stock_level', 'last_updated']
    list_filter = ['batch__medicine__manufacturer', 'last_updated']
    search_fields = ['batch__medicine__name', 'batch__batch_number']
    readonly_fields = ['available_stock', 'needs_restock']

@admin.register(MedicineTransfer)
class MedicineTransferAdmin(admin.ModelAdmin):
    list_display = ['transfer_type', 'from_user', 'to_user', 'batch', 'quantity', 'transfer_date', 'is_completed']
    list_filter = ['transfer_type', 'transfer_date', 'is_completed']
    search_fields = ['from_user__username', 'to_user__username', 'batch__medicine__name']
    readonly_fields = ['transfer_date']


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ['name', 'manufacturer', 'is_primary']
    list_filter = ['is_primary']
    search_fields = ['name', 'manufacturer__username']

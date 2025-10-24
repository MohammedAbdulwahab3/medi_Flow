from django.contrib import admin
from .models import Medicine, MedicineBatch

@admin.register(Medicine)
class MedicineAdmin(admin.ModelAdmin):
    list_display = ('name', 'generic_name', 'strength', 'dosage_form', 'manufacturer', 'is_active', 'created_at')
    list_filter = ('dosage_form', 'is_active', 'manufacturer', 'created_at')
    search_fields = ('name', 'generic_name', 'description')
    list_editable = ('is_active',)
    readonly_fields = ('created_at', 'updated_at')
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = 'Manage Medicines'
        return super().changelist_view(request, extra_context=extra_context)
    
    def add_view(self, request, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = 'Add Medicine'
        return super().add_view(request, form_url, extra_context=extra_context)


@admin.register(MedicineBatch)
class MedicineBatchAdmin(admin.ModelAdmin):
    list_display = ('medicine', 'batch_number', 'quantity', 'manufacturing_date', 'expiry_date', 'cost_price', 'selling_price', 'is_active')
    list_filter = ('is_active', 'manufacturing_date', 'expiry_date', 'medicine__dosage_form')
    search_fields = ('batch_number', 'medicine__name')
    list_editable = ('is_active', 'cost_price', 'selling_price')
    readonly_fields = ('created_at',)
    date_hierarchy = 'manufacturing_date'
    
    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = 'Manage Medicine Batches'
        return super().changelist_view(request, extra_context=extra_context)
    
    def add_view(self, request, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['title'] = 'Add Medicine Batch'
        return super().add_view(request, form_url, extra_context=extra_context)

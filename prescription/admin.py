from django.contrib import admin
from .models import Prescription, PatientMedicalRecord, PatientHistoryEntry

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'medicine', 'dosage', 'quantity', 'prescribed_date', 'status', 'dispensed_by')
    list_filter = ('status', 'prescribed_date', 'medicine__dosage_form')
    search_fields = ('patient__username', 'doctor__username', 'medicine__name')
    list_editable = ('status',)
    readonly_fields = ('prescribed_date',)
    date_hierarchy = 'prescribed_date'


@admin.register(PatientMedicalRecord)
class PatientMedicalRecordAdmin(admin.ModelAdmin):
    list_display = ('patient', 'blood_type', 'last_updated')
    search_fields = ('patient__username', 'allergies', 'chronic_conditions')


@admin.register(PatientHistoryEntry)
class PatientHistoryEntryAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'visit_date')
    search_fields = ('patient__username', 'doctor__username', 'case_summary', 'diagnosis')
    date_hierarchy = 'visit_date'
    readonly_fields = ()

    def has_change_permission(self, request, obj=None):
        # Prevent editing existing entries via admin; allow viewing list
        if obj is not None:
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        # Prevent deleting existing entries via admin
        return False

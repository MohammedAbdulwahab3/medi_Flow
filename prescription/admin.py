from django.contrib import admin
from .models import (
    Prescription, PatientMedicalRecord, PatientHistoryEntry,
    DoctorProfile, PatientDoctorAssignment, Message, Notification
)

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


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'years_of_experience', 'consultation_fee')
    search_fields = ('user__username', 'user__full_name', 'specialization')
    list_filter = ('specialization',)


@admin.register(PatientDoctorAssignment)
class PatientDoctorAssignmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'assigned_date', 'is_primary')
    list_filter = ('is_primary', 'assigned_date')
    search_fields = ('patient__username', 'doctor__username')
    date_hierarchy = 'assigned_date'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('sender', 'recipient', 'subject', 'sent_at', 'is_read')
    list_filter = ('is_read', 'sent_at')
    search_fields = ('sender__username', 'recipient__username', 'subject', 'body')
    date_hierarchy = 'sent_at'
    readonly_fields = ('sent_at',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'notification_type', 'title', 'created_at', 'is_read')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'title', 'message')
    date_hierarchy = 'created_at'
    readonly_fields = ('created_at',)

from django.db import models
from django.conf import settings
from medicine.models import Medicine
from medicine.models import MedicineBatch

class Prescription(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('dispensed', 'Dispensed'),
        ('cancelled', 'Cancelled'),
    ]
    
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='patient_prescriptions'
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='doctor_prescriptions'
    )
    dispensed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='dispensed_prescriptions'
    )
    medicine = models.ForeignKey(Medicine, on_delete=models.CASCADE)
    dosage = models.CharField(max_length=100)
    duration = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    prescribed_date = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    notes = models.TextField(blank=True)
    dispensed_date = models.DateTimeField(null=True, blank=True)
    dispensed_batch = models.ForeignKey(MedicineBatch, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-prescribed_date']
    
    def __str__(self):
        return f"{self.patient.username} - {self.medicine.name} ({self.status})"


class PatientMedicalRecord(models.Model):
    BLOOD_TYPES = [
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ]

    patient = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='medical_record')
    blood_type = models.CharField(max_length=3, choices=BLOOD_TYPES, blank=True, null=True)
    allergies = models.TextField(blank=True)
    chronic_conditions = models.TextField(blank=True)
    past_surgeries = models.TextField(blank=True)
    current_medications = models.TextField(blank=True)
    family_history = models.TextField(blank=True)
    social_history = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    last_updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Medical Record for {self.patient.username}"


class PatientHistoryEntry(models.Model):
    patient = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='history_entries')
    doctor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='authored_history_entries')
    visit_date = models.DateTimeField(auto_now_add=True)
    case_summary = models.TextField()
    diagnosis = models.TextField(blank=True)
    treatment_plan = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-visit_date']

    def __str__(self):
        return f"{self.patient} - {self.visit_date:%Y-%m-%d} by {self.doctor}"


class DoctorProfile(models.Model):
    """Extended profile for doctors with e-signature and specialization"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='doctor_profile')
    specialization = models.CharField(max_length=255, blank=True)
    qualifications = models.TextField(blank=True)
    e_signature = models.TextField(blank=True, help_text="Digital signature text")
    years_of_experience = models.PositiveIntegerField(default=0)
    consultation_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    available_days = models.CharField(max_length=255, blank=True, help_text="e.g., Mon-Fri")
    available_hours = models.CharField(max_length=255, blank=True, help_text="e.g., 9AM-5PM")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Dr. {self.user.full_name or self.user.username}"


class PatientDoctorAssignment(models.Model):
    """Track which doctors are assigned to which patients"""
    patient = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='doctor_assignments',
        limit_choices_to={'role': 'patient'}
    )
    doctor = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='patient_assignments',
        limit_choices_to={'role': 'doctor'}
    )
    assigned_date = models.DateTimeField(auto_now_add=True)
    is_primary = models.BooleanField(default=False, help_text="Is this the primary doctor?")
    notes = models.TextField(blank=True)

    class Meta:
        unique_together = ['patient', 'doctor']
        ordering = ['-is_primary', '-assigned_date']

    def __str__(self):
        return f"{self.patient.username} -> Dr. {self.doctor.full_name or self.doctor.username}"


class Message(models.Model):
    """Direct messaging between doctors and patients"""
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='sent_messages'
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='received_messages'
    )
    subject = models.CharField(max_length=255, blank=True)
    body = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    parent_message = models.ForeignKey(
        'self', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True, 
        related_name='replies'
    )

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f"{self.sender.username} -> {self.recipient.username}: {self.subject[:50]}"


class Notification(models.Model):
    """Notification system for prescriptions and other events"""
    NOTIFICATION_TYPES = [
        ('prescription_created', 'Prescription Created'),
        ('prescription_dispensed', 'Prescription Dispensed'),
        ('prescription_cancelled', 'Prescription Cancelled'),
        ('message_received', 'Message Received'),
        ('appointment_reminder', 'Appointment Reminder'),
        ('doctor_assigned', 'Doctor Assigned'),
        # Inventory & Transfer notifications
        ('transfer_received', 'Transfer Received'),
        ('transfer_accepted', 'Transfer Accepted'),
        ('reservation_request', 'Reservation Request'),
        ('reservation_approved', 'Reservation Approved'),
        ('reservation_rejected', 'Reservation Rejected'),
        ('low_stock_alert', 'Low Stock Alert'),
        ('expiry_warning', 'Expiry Warning'),
        ('reorder_alert', 'Reorder Alert'),
        # General
        ('system_announcement', 'System Announcement'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='notifications'
    )
    notification_type = models.CharField(max_length=50, choices=NOTIFICATION_TYPES)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    related_prescription = models.ForeignKey(
        'Prescription', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    related_message = models.ForeignKey(
        'Message', 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    # Additional related objects for comprehensive notifications
    related_object_id = models.PositiveIntegerField(null=True, blank=True, help_text="Generic FK for related objects")
    related_object_type = models.CharField(max_length=50, blank=True, default='', help_text="Type: transfer, reservation, batch, etc.")
    action_url = models.CharField(max_length=500, blank=True, default='', help_text="Direct link to action page")

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username}: {self.title}"

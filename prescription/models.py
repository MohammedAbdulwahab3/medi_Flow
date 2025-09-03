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


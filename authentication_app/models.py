from django.db import models
import uuid as uuid_lib
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    uuid = models.UUIDField(default=uuid_lib.uuid4, editable=False, unique=True)
    ROLE_ADMIN = 'admin'
    ROLE_DOCTOR = 'doctor'
    ROLE_PHARMACIST = 'pharmacist'
    ROLE_MANUFACTURER = 'manufacturer'
    ROLE_PATIENT = 'patient'

    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin'),
        (ROLE_DOCTOR, 'Doctor'),
        (ROLE_PHARMACIST, 'Pharmacist'),
        (ROLE_MANUFACTURER, 'Manufacturer'),
        (ROLE_PATIENT, 'Patient'),
    ]

    role = models.CharField(max_length=30, choices=ROLE_CHOICES, default=ROLE_PATIENT)
    license_number = models.CharField(max_length=150, blank=True, null=True, unique=True)
    national_id = models.CharField(max_length=50, blank=True, null=True, unique=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

    @property
    def is_doctor(self):
        return self.role == self.ROLE_DOCTOR

    @property
    def is_pharmacist(self):
        return self.role == self.ROLE_PHARMACIST

    @property
    def is_manufacturer(self):
        return self.role == self.ROLE_MANUFACTURER

    @property
    def is_patient(self):
        return self.role == self.ROLE_PATIENT


class PharmacistProfile(models.Model):
    user = models.OneToOneField('authentication_app.User', on_delete=models.CASCADE, related_name='pharmacist_profile')
    pharmacy_name = models.CharField(max_length=255, blank=True)
    address = models.CharField(max_length=255, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    phone = models.CharField(max_length=50, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.pharmacy_name or f"Pharmacy of {self.user.username}"

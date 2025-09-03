from django import template
from django.db.models import Count, Sum, F
from django.utils import timezone

from authentication_app.models import User
from medicine.models import MedicineBatch
from prescription.models import Prescription
from inventory.models import MedicineTransfer

register = template.Library()


@register.simple_tag
def analytics():
    # Users by role
    data = {}
    data['total_users'] = User.objects.count()
    data['doctors'] = User.objects.filter(role=User.ROLE_DOCTOR).count()
    data['pharmacists'] = User.objects.filter(role=User.ROLE_PHARMACIST).count()
    data['manufacturers'] = User.objects.filter(role=User.ROLE_MANUFACTURER).count()
    data['patients'] = User.objects.filter(role=User.ROLE_PATIENT).count()

    # Medicines / batches
    data['medicines'] = MedicineBatch.objects.values('medicine').distinct().count()
    soon = timezone.now().date() + timezone.timedelta(days=30)
    data['expiring_batches'] = MedicineBatch.objects.filter(expiry_date__lte=soon).count()

    # Prescriptions
    data['prescriptions_pending'] = Prescription.objects.filter(status='pending').count()
    data['prescriptions_dispensed'] = Prescription.objects.filter(status='dispensed').count()
    data['prescriptions_cancelled'] = Prescription.objects.filter(status='cancelled').count()

    # Transfers
    data['transfers_pending'] = MedicineTransfer.objects.filter(is_completed=False).count()
    data['transfers_completed'] = MedicineTransfer.objects.filter(is_completed=True).count()

    return data


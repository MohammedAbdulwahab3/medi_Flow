from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.utils import timezone
from .models import Prescription, Message, Notification, DoctorProfile, PatientDoctorAssignment


@receiver(post_save, sender=Prescription)
def create_prescription_notification(sender, instance, created, **kwargs):
    """Create notification when prescription is created or dispensed"""
    if created:
        # Notify patient about new prescription
        Notification.objects.create(
            user=instance.patient,
            notification_type='prescription_created',
            title='New Prescription',
            message=f'Dr. {instance.doctor.full_name or instance.doctor.username} has prescribed {instance.medicine.name}. '
                   f'Dosage: {instance.dosage}. Duration: {instance.duration}.',
            related_prescription=instance
        )
        
        # Auto-assign doctor to patient if not already assigned
        PatientDoctorAssignment.objects.get_or_create(
            patient=instance.patient,
            doctor=instance.doctor,
            defaults={'is_primary': False}
        )
    
    # Check if prescription was dispensed (status changed to dispensed)
    if not created and instance.status == 'dispensed' and instance.dispensed_date:
        # Check if notification already exists for this dispensed prescription
        existing = Notification.objects.filter(
            user=instance.patient,
            notification_type='prescription_dispensed',
            related_prescription=instance
        ).exists()
        
        if not existing:
            # Notify patient about dispensed prescription
            Notification.objects.create(
                user=instance.patient,
                notification_type='prescription_dispensed',
                title='Prescription Dispensed',
                message=f'Your prescription for {instance.medicine.name} has been dispensed by {instance.dispensed_by.full_name or instance.dispensed_by.username}.',
                related_prescription=instance
            )
            
            # Notify doctor about dispensed prescription
            Notification.objects.create(
                user=instance.doctor,
                notification_type='prescription_dispensed',
                title='Prescription Dispensed',
                message=f'Prescription for {instance.patient.full_name or instance.patient.username} ({instance.medicine.name}) has been dispensed.',
                related_prescription=instance
            )


@receiver(post_save, sender=Message)
def create_message_notification(sender, instance, created, **kwargs):
    """Create notification when message is received"""
    if created:
        Notification.objects.create(
            user=instance.recipient,
            notification_type='message_received',
            title='New Message',
            message=f'You have a new message from {instance.sender.full_name or instance.sender.username}: {instance.subject}',
            related_message=instance
        )


@receiver(post_save, sender=PatientDoctorAssignment)
def create_assignment_notification(sender, instance, created, **kwargs):
    """Create notification when doctor is assigned to patient"""
    if created:
        Notification.objects.create(
            user=instance.patient,
            notification_type='doctor_assigned',
            title='Doctor Assigned',
            message=f'Dr. {instance.doctor.full_name or instance.doctor.username} has been assigned as your {"primary " if instance.is_primary else ""}doctor.'
        )


@receiver(post_save, sender='authentication_app.User')
def create_doctor_profile(sender, instance, created, **kwargs):
    """Automatically create doctor profile for new doctors"""
    if instance.role == 'doctor' and not hasattr(instance, 'doctor_profile'):
        DoctorProfile.objects.get_or_create(user=instance)

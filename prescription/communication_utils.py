"""
Communication utilities for messaging and notifications across all user roles
"""
from django.utils import timezone
from django.urls import reverse
from .models import Message, Notification


def send_message(sender, recipient, subject, body, parent_message=None):
    """
    Send a message from one user to another
    
    Args:
        sender: User object (sender)
        recipient: User object (recipient)
        subject: str (message subject)
        body: str (message body)
        parent_message: Message object (for replies)
    
    Returns:
        Message object
    """
    message = Message.objects.create(
        sender=sender,
        recipient=recipient,
        subject=subject,
        body=body,
        parent_message=parent_message
    )
    
    # Create notification for recipient
    create_notification(
        user=recipient,
        notification_type='message_received',
        title=f'New message from {sender.full_name or sender.username}',
        message=f'Subject: {subject}',
        related_message=message,
        action_url=reverse('prescription:message_detail', kwargs={'message_id': message.id})
    )
    
    return message


def create_notification(user, notification_type, title, message, 
                       related_prescription=None, related_message=None,
                       related_object_id=None, related_object_type=None,
                       action_url=None):
    """
    Create a notification for a user
    
    Args:
        user: User object
        notification_type: str (from Notification.NOTIFICATION_TYPES)
        title: str
        message: str
        related_prescription: Prescription object (optional)
        related_message: Message object (optional)
        related_object_id: int (optional, for generic relationships)
        related_object_type: str (optional, e.g., 'transfer', 'reservation')
        action_url: str (optional, direct link to action page)
    
    Returns:
        Notification object
    """
    notification = Notification.objects.create(
        user=user,
        notification_type=notification_type,
        title=title,
        message=message,
        related_prescription=related_prescription,
        related_message=related_message,
        related_object_id=related_object_id,
        related_object_type=related_object_type or '',  # Default to empty string
        action_url=action_url or ''  # Default to empty string
    )
    
    return notification


def notify_transfer_received(transfer):
    """Notify recipient about incoming transfer"""
    create_notification(
        user=transfer.to_user,
        notification_type='transfer_received',
        title=f'Transfer Received from {transfer.from_user.full_name or transfer.from_user.username}',
        message=f'You have received {transfer.quantity} units of {transfer.batch.medicine.name} (Batch: {transfer.batch.batch_number})',
        related_object_id=transfer.id,
        related_object_type='transfer',
        action_url=reverse('frontend:pharmacist_transfers')
    )


def notify_transfer_accepted(transfer):
    """Notify sender that transfer was accepted"""
    create_notification(
        user=transfer.from_user,
        notification_type='transfer_accepted',
        title=f'Transfer Accepted by {transfer.to_user.full_name or transfer.to_user.username}',
        message=f'Your transfer of {transfer.quantity} units of {transfer.batch.medicine.name} has been accepted',
        related_object_id=transfer.id,
        related_object_type='transfer',
        action_url=reverse('frontend:transfer_medicine')
    )


def notify_reservation_request(reservation):
    """Notify manufacturer about new reservation request"""
    create_notification(
        user=reservation.manufacturer,
        notification_type='reservation_request',
        title=f'New Reservation Request from {reservation.pharmacy.full_name or reservation.pharmacy.username}',
        message=f'Request for {reservation.quantity} units of {reservation.medicine.name}',
        related_object_id=reservation.id,
        related_object_type='reservation',
        action_url=reverse('frontend:manufacturer_reservations')
    )


def notify_reservation_approved(reservation):
    """Notify pharmacy that reservation was approved"""
    create_notification(
        user=reservation.pharmacy,
        notification_type='reservation_approved',
        title='Reservation Request Approved',
        message=f'Your request for {reservation.quantity} units of {reservation.medicine.name} has been approved',
        related_object_id=reservation.id,
        related_object_type='reservation',
        action_url=reverse('frontend:pharmacist_reservations')
    )


def notify_reservation_rejected(reservation):
    """Notify pharmacy that reservation was rejected"""
    create_notification(
        user=reservation.pharmacy,
        notification_type='reservation_rejected',
        title='Reservation Request Rejected',
        message=f'Your request for {reservation.quantity} units of {reservation.medicine.name} was not approved',
        related_object_id=reservation.id,
        related_object_type='reservation',
        action_url=reverse('frontend:pharmacist_reservations')
    )


def notify_low_stock(pharmacist, inventory_item):
    """Notify pharmacist about low stock"""
    create_notification(
        user=pharmacist,
        notification_type='low_stock_alert',
        title='Low Stock Alert',
        message=f'{inventory_item.batch.medicine.name} is running low (Current: {inventory_item.current_stock} units)',
        related_object_id=inventory_item.id,
        related_object_type='pharmacy_inventory',
        action_url=reverse('frontend:pharmacist_inventory')
    )


def notify_expiry_warning(pharmacist, inventory_item, days_until_expiry):
    """Notify pharmacist about expiring medicine"""
    create_notification(
        user=pharmacist,
        notification_type='expiry_warning',
        title='Medicine Expiring Soon',
        message=f'{inventory_item.batch.medicine.name} (Batch: {inventory_item.batch.batch_number}) will expire in {days_until_expiry} days',
        related_object_id=inventory_item.id,
        related_object_type='pharmacy_inventory',
        action_url=reverse('frontend:pharmacist_inventory')
    )


def notify_prescription_dispensed(prescription):
    """Notify patient and doctor when prescription is dispensed"""
    # Notify patient
    create_notification(
        user=prescription.patient,
        notification_type='prescription_dispensed',
        title='Prescription Ready',
        message=f'Your prescription for {prescription.medicine.name} has been dispensed',
        related_prescription=prescription,
        action_url=reverse('prescription:patient_mine')
    )
    
    # Notify doctor
    create_notification(
        user=prescription.doctor,
        notification_type='prescription_dispensed',
        title='Prescription Dispensed',
        message=f'Prescription for {prescription.patient.full_name or prescription.patient.username} ({prescription.medicine.name}) has been dispensed',
        related_prescription=prescription,
        action_url=reverse('prescription:doctor_list')
    )


def get_contactable_users(current_user):
    """
    Get list of users that current user can message
    
    Returns dict with categories:
    - pharmacists: for manufacturers, doctors, patients
    - manufacturers: for pharmacists
    - doctors: for pharmacists, patients
    - patients: for doctors, pharmacists
    """
    from authentication_app.models import User
    
    contacts = {
        'pharmacists': [],
        'manufacturers': [],
        'doctors': [],
        'patients': []
    }
    
    if current_user.is_manufacturer:
        # Manufacturers can contact pharmacists who have requested from them
        from inventory.models import ReservationRequest, MedicineTransfer
        pharmacist_ids = set()
        pharmacist_ids.update(
            ReservationRequest.objects.filter(manufacturer=current_user)
            .values_list('pharmacy_id', flat=True)
        )
        pharmacist_ids.update(
            MedicineTransfer.objects.filter(from_user=current_user, transfer_type='manufacturer_to_pharmacy')
            .values_list('to_user_id', flat=True)
        )
        contacts['pharmacists'] = User.objects.filter(id__in=pharmacist_ids).order_by('username')
    
    elif current_user.is_pharmacist:
        # Pharmacists can contact:
        # 1. Manufacturers they've interacted with
        from inventory.models import ReservationRequest, MedicineTransfer
        manufacturer_ids = set()
        manufacturer_ids.update(
            ReservationRequest.objects.filter(pharmacy=current_user)
            .values_list('manufacturer_id', flat=True)
        )
        manufacturer_ids.update(
            MedicineTransfer.objects.filter(to_user=current_user, transfer_type='manufacturer_to_pharmacy')
            .values_list('from_user_id', flat=True)
        )
        contacts['manufacturers'] = User.objects.filter(id__in=manufacturer_ids).order_by('username')
        
        # 2. Patients with prescriptions
        from prescription.models import Prescription
        patient_ids = Prescription.objects.filter(
            dispensed_by=current_user
        ).values_list('patient_id', flat=True).distinct()
        contacts['patients'] = User.objects.filter(id__in=patient_ids).order_by('username')
        
        # 3. All doctors (for prescription queries)
        contacts['doctors'] = User.objects.filter(role=User.ROLE_DOCTOR).order_by('username')
    
    elif current_user.is_doctor:
        # Doctors can contact their patients and pharmacists
        from prescription.models import PatientDoctorAssignment, Prescription
        patient_ids = PatientDoctorAssignment.objects.filter(
            doctor=current_user
        ).values_list('patient_id', flat=True)
        contacts['patients'] = User.objects.filter(id__in=patient_ids).order_by('username')
        
        # Pharmacists who dispensed their prescriptions
        pharmacist_ids = Prescription.objects.filter(
            doctor=current_user,
            dispensed_by__isnull=False
        ).values_list('dispensed_by_id', flat=True).distinct()
        contacts['pharmacists'] = User.objects.filter(id__in=pharmacist_ids).order_by('username')
    
    elif current_user.is_patient:
        # Patients can contact their doctors and pharmacists who dispensed
        from prescription.models import PatientDoctorAssignment, Prescription
        doctor_ids = PatientDoctorAssignment.objects.filter(
            patient=current_user
        ).values_list('doctor_id', flat=True)
        contacts['doctors'] = User.objects.filter(id__in=doctor_ids).order_by('username')
        
        pharmacist_ids = Prescription.objects.filter(
            patient=current_user,
            dispensed_by__isnull=False
        ).values_list('dispensed_by_id', flat=True).distinct()
        contacts['pharmacists'] = User.objects.filter(id__in=pharmacist_ids).order_by('username')
    
    return contacts

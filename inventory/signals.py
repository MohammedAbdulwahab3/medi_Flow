from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import MedicineTransfer, PharmacyInventory, ReservationRequest
from prescription.communication_utils import (
    notify_transfer_received, notify_transfer_accepted,
    notify_reservation_request, notify_reservation_approved,
    notify_reservation_rejected
)


@receiver(post_save, sender=MedicineTransfer)
def create_pharmacy_inventory_on_transfer(sender, instance: MedicineTransfer, created: bool, **kwargs):
    # When a transfer is created to a pharmacist, ensure a PharmacyInventory row exists
    if created and instance.to_user and instance.to_user.is_pharmacist:
        PharmacyInventory.objects.get_or_create(
            pharmacist=instance.to_user,
            batch=instance.batch,
            defaults={'current_stock': 0}
        )
        # Send notification to recipient
        notify_transfer_received(instance)


@receiver(pre_save, sender=MedicineTransfer)
def apply_completed_transfer_to_inventory(sender, instance: MedicineTransfer, **kwargs):
    # If marking a transfer as completed (False -> True), increment pharmacist stock automatically
    if not instance.pk:
        return
    try:
        previous = MedicineTransfer.objects.get(pk=instance.pk)
    except MedicineTransfer.DoesNotExist:
        return
    if not previous.is_completed and instance.is_completed:
        if instance.to_user and instance.to_user.is_pharmacist:
            inv, _ = PharmacyInventory.objects.get_or_create(
                pharmacist=instance.to_user,
                batch=instance.batch,
                defaults={'current_stock': 0}
            )
            inv.current_stock = (inv.current_stock or 0) + (instance.quantity or 0)
            inv.save()
            # Send notification to sender
            notify_transfer_accepted(instance)


@receiver(post_save, sender=ReservationRequest)
def notify_reservation_request_created(sender, instance: ReservationRequest, created: bool, **kwargs):
    """Notify manufacturer when reservation request is created"""
    if created:
        notify_reservation_request(instance)


@receiver(pre_save, sender=ReservationRequest)
def notify_reservation_status_change(sender, instance: ReservationRequest, **kwargs):
    """Notify pharmacy when reservation status changes"""
    if not instance.pk:
        return
    try:
        previous = ReservationRequest.objects.get(pk=instance.pk)
    except ReservationRequest.DoesNotExist:
        return
    
    # Status changed from pending to reserved
    if previous.status == ReservationRequest.STATUS_PENDING and instance.status == ReservationRequest.STATUS_RESERVED:
        notify_reservation_approved(instance)
    
    # Status changed to rejected
    elif previous.status == ReservationRequest.STATUS_PENDING and instance.status == ReservationRequest.STATUS_REJECTED:
        notify_reservation_rejected(instance)


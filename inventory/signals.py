from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

from .models import MedicineTransfer, PharmacyInventory


@receiver(post_save, sender=MedicineTransfer)
def create_pharmacy_inventory_on_transfer(sender, instance: MedicineTransfer, created: bool, **kwargs):
    # When a transfer is created to a pharmacist, ensure a PharmacyInventory row exists
    if created and instance.to_user and instance.to_user.is_pharmacist:
        PharmacyInventory.objects.get_or_create(
            pharmacist=instance.to_user,
            batch=instance.batch,
            defaults={'current_stock': 0}
        )


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


# Generated migration for PharmacyInventory selling_price field

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('inventory', '0004_alter_reservationrequest_status'),
    ]

    operations = [
        migrations.AddField(
            model_name='pharmacyinventory',
            name='selling_price',
            field=models.DecimalField(blank=True, decimal_places=2, help_text="Pharmacy's selling price (if different from batch price)", max_digits=10, null=True),
        ),
    ]

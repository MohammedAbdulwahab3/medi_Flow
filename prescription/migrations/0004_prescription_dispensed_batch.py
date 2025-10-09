from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('medicine', '0001_initial'),
        ('prescription', '0003_patienthistoryentry'),
    ]

    operations = [
        migrations.AddField(
            model_name='prescription',
            name='dispensed_batch',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='medicine.medicinebatch'),
        ),
    ]



from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('prescription', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PatientMedicalRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('blood_type', models.CharField(blank=True, choices=[('A+', 'A+'), ('A-', 'A-'), ('B+', 'B+'), ('B-', 'B-'), ('AB+', 'AB+'), ('AB-', 'AB-'), ('O+', 'O+'), ('O-', 'O-')], max_length=3, null=True)),
                ('allergies', models.TextField(blank=True)),
                ('chronic_conditions', models.TextField(blank=True)),
                ('past_surgeries', models.TextField(blank=True)),
                ('current_medications', models.TextField(blank=True)),
                ('family_history', models.TextField(blank=True)),
                ('social_history', models.TextField(blank=True)),
                ('notes', models.TextField(blank=True)),
                ('last_updated', models.DateTimeField(auto_now=True)),
                ('patient', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='medical_record', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]



# Generated migration for enhanced notification system

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prescription', '0005_message_notification_doctorprofile_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='notification',
            name='notification_type',
            field=models.CharField(
                max_length=50,
                choices=[
                    ('prescription_created', 'Prescription Created'),
                    ('prescription_dispensed', 'Prescription Dispensed'),
                    ('prescription_cancelled', 'Prescription Cancelled'),
                    ('message_received', 'Message Received'),
                    ('appointment_reminder', 'Appointment Reminder'),
                    ('doctor_assigned', 'Doctor Assigned'),
                    ('transfer_received', 'Transfer Received'),
                    ('transfer_accepted', 'Transfer Accepted'),
                    ('reservation_request', 'Reservation Request'),
                    ('reservation_approved', 'Reservation Approved'),
                    ('reservation_rejected', 'Reservation Rejected'),
                    ('low_stock_alert', 'Low Stock Alert'),
                    ('expiry_warning', 'Expiry Warning'),
                    ('reorder_alert', 'Reorder Alert'),
                    ('system_announcement', 'System Announcement'),
                ]
            ),
        ),
        migrations.AddField(
            model_name='notification',
            name='related_object_id',
            field=models.PositiveIntegerField(
                null=True,
                blank=True,
                help_text='Generic FK for related objects'
            ),
        ),
        migrations.AddField(
            model_name='notification',
            name='related_object_type',
            field=models.CharField(
                max_length=50,
                blank=True,
                default='',
                help_text='Type: transfer, reservation, batch, etc.'
            ),
        ),
        migrations.AddField(
            model_name='notification',
            name='action_url',
            field=models.CharField(
                max_length=500,
                blank=True,
                default='',
                help_text='Direct link to action page'
            ),
        ),
    ]

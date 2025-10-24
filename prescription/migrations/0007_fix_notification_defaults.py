# Fix for IntegrityError: Add default values to notification fields

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('prescription', '0006_enhance_notifications'),
    ]

    operations = [
        # Update existing NULL values to empty strings
        migrations.RunSQL(
            sql="UPDATE prescription_notification SET related_object_type = '' WHERE related_object_type IS NULL;",
            reverse_sql="UPDATE prescription_notification SET related_object_type = NULL WHERE related_object_type = '';",
        ),
        migrations.RunSQL(
            sql="UPDATE prescription_notification SET action_url = '' WHERE action_url IS NULL;",
            reverse_sql="UPDATE prescription_notification SET action_url = NULL WHERE action_url = '';",
        ),
        
        # Alter fields to have default values
        migrations.AlterField(
            model_name='notification',
            name='related_object_type',
            field=models.CharField(
                max_length=50,
                blank=True,
                default='',
                help_text='Type: transfer, reservation, batch, etc.'
            ),
        ),
        migrations.AlterField(
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

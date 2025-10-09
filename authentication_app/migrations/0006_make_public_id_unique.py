from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('authentication_app', '0005_populate_public_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='public_id',
            field=models.CharField(default='UNKNOWN', editable=False, max_length=12, unique=True),
        ),
    ]

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('authentication_app', '0002_pharmacistprofile'),
    ]

    def gen_uuid_for_existing_users(apps, schema_editor):
        User = apps.get_model('authentication_app', 'User')
        for user in User.objects.all():
            if getattr(user, 'uuid', None) in (None, ''):
                user.uuid = uuid.uuid4()
                user.save(update_fields=['uuid'])

    operations = [
        # Add uuid as nullable first to avoid unique/default collisions during table rewrite
        migrations.AddField(
            model_name='user',
            name='uuid',
            field=models.UUIDField(null=True, editable=False),
        ),
        migrations.AddField(
            model_name='user',
            name='national_id',
            field=models.CharField(blank=True, max_length=50, null=True, unique=True),
        ),
        migrations.RunPython(gen_uuid_for_existing_users, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='user',
            name='uuid',
            field=models.UUIDField(default=uuid.uuid4, editable=False, unique=True),
        ),
    ]



from django.db import migrations
import random


def gen_public_id():
    return ''.join(random.choices('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789', k=10))


def populate_public_ids(apps, schema_editor):
    User = apps.get_model('authentication_app', 'User')
    existing = set(User.objects.exclude(public_id__isnull=True).values_list('public_id', flat=True))
    for u in User.objects.all():
        if not u.public_id:
            pid = gen_public_id()
            while pid in existing:
                pid = gen_public_id()
            u.public_id = pid
            u.save(update_fields=['public_id'])
            existing.add(pid)


class Migration(migrations.Migration):

    dependencies = [
        ('authentication_app', '0004_user_address_user_date_of_birth_and_more'),
    ]

    operations = [
        migrations.RunPython(populate_public_ids),
    ]

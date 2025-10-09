# Generated migration for medicine model updates

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('medicine', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='medicine',
            name='category',
            field=models.CharField(choices=[('pain_relief', 'Pain Relief'), ('antibiotics', 'Antibiotics'), ('cardiovascular', 'Cardiovascular'), ('diabetes', 'Diabetes'), ('respiratory', 'Respiratory'), ('gastrointestinal', 'Gastrointestinal'), ('vitamins', 'Vitamins & Supplements'), ('skin_care', 'Skin Care'), ('other', 'Other')], default='other', max_length=50),
        ),
        migrations.AddField(
            model_name='medicine',
            name='image',
            field=models.URLField(blank=True, help_text='URL to medicine image', max_length=500, null=True),
        ),
    ]

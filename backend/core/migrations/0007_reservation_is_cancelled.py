# Generated by Django 5.2.1 on 2025-06-19 16:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0006_alter_customuser_birth_date'),
    ]

    operations = [
        migrations.AddField(
            model_name='reservation',
            name='is_cancelled',
            field=models.BooleanField(default=False),
        ),
    ]

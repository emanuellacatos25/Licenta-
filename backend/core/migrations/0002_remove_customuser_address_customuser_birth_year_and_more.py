# Generated by Django 5.2.1 on 2025-06-11 21:45

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customuser',
            name='address',
        ),
        migrations.AddField(
            model_name='customuser',
            name='birth_year',
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='cnp',
            field=models.CharField(blank=True, max_length=13, null=True),
        ),
    ]

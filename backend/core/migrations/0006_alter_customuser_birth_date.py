from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_reservation_is_validated'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customuser',
            name='birth_date',
        ),
        migrations.AddField(
            model_name='customuser',
            name='birth_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]

# Generated by Django 5.0.6 on 2024-09-19 17:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0002_jobpost_is_paid_jobpost_payment_order'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobpost',
            name='posting_cost',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
    ]

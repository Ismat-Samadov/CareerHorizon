# Generated by Django 5.0.6 on 2024-09-19 16:40

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0002_jobpost_is_paid_jobpost_payment_order'),
        ('payments', '0002_alter_order_status_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='job',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='jobs.jobpost'),
        ),
    ]

# Generated by Django 5.1.7 on 2025-03-23 19:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0002_alter_users_role'),
    ]

    operations = [
        migrations.AddField(
            model_name='users',
            name='saldo',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
    ]

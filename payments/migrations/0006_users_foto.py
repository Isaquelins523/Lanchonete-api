# Generated by Django 5.1.7 on 2025-03-24 14:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('payments', '0005_users_id_aluno'),
    ]

    operations = [
        migrations.AddField(
            model_name='users',
            name='foto',
            field=models.ImageField(blank=True, null=True, upload_to='alunos_fotos/'),
        ),
    ]

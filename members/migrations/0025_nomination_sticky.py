# Generated by Django 2.2.13 on 2020-06-11 13:29

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('members', '0024_auto_20200527_1550'),
    ]

    operations = [
        migrations.AddField(
            model_name='nomination',
            name='sticky',
            field=models.BooleanField(default=False, help_text="Non supprimé par l'import du portail", verbose_name='Collant'),
        ),
    ]

# Generated by Django 2.1.7 on 2019-08-18 17:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0030_auto_20190814_0856'),
    ]

    operations = [
        migrations.AddField(
            model_name='thirdparty',
            name='account',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='accounting.Account', verbose_name='Compte principal'),
        ),
    ]

# Generated by Django 2.1.7 on 2019-07-03 06:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0019_auto_20190213_2143'),
    ]

    operations = [
        migrations.AlterField(
            model_name='entry',
            name='scan',
            field=models.FileField(blank=True, upload_to='justificatif', verbose_name='Justificatif'),
        ),
    ]

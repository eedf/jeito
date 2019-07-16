# Generated by Django 2.1.7 on 2019-07-16 13:57

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0022_auto_20190710_1719'),
    ]

    operations = [
        migrations.AlterField(
            model_name='entry',
            name='date',
            field=models.DateField(default=datetime.date.today, verbose_name='Date'),
        ),
        migrations.AlterField(
            model_name='transferorder',
            name='xml',
            field=models.TextField(editable=False),
        ),
    ]

# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-07 13:11
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='analytic',
            options={'verbose_name': 'Analytique'},
        ),
    ]

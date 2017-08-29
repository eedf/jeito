# -*- coding: utf-8 -*-
# Generated by Django 1.11.2 on 2017-08-29 15:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Action',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=100, verbose_name='Titre')),
                ('description', models.TextField()),
                ('deadline', models.DateField(blank=True, null=True, verbose_name='Date limite')),
                ('done', models.BooleanField(default=False, verbose_name='Fait')),
                ('creation', models.DateTimeField(auto_now_add=True, verbose_name='Date de création')),
            ],
        ),
    ]

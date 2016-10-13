# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-10-12 16:48
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Group',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('type', models.IntegerField(choices=[(1, 'EEDF'), (2, 'Scout'), (3, 'Extérieur')])),
                ('name', models.CharField(max_length=100)),
                ('firstname', models.CharField(blank=True, max_length=100)),
                ('lastname', models.CharField(blank=True, max_length=100)),
                ('tel', models.CharField(blank=True, max_length=100)),
                ('email', models.EmailField(blank=True, max_length=254)),
            ],
        ),
        migrations.CreateModel(
            name='Headcount',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('number', models.PositiveIntegerField()),
                ('begin', models.DateField()),
                ('end', models.DateField()),
                ('comfort', models.IntegerField(choices=[(1, 'Terrain'), (2, 'Village')])),
                ('group', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='headcounts', to='becours.Group')),
            ],
        ),
    ]

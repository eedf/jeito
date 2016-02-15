# -*- coding: utf-8 -*-
# Generated by Django 1.9.2 on 2016-02-15 21:44
from __future__ import unicode_literals

from django.db import migrations, models
import tagulous.models.fields
import tagulous.models.models


class Migration(migrations.Migration):

    dependencies = [
        ('docs', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='DocumentTags',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
                ('slug', models.SlugField()),
                ('count', models.IntegerField(default=0, help_text='Internal counter of how many times this tag is in use')),
                ('protected', models.BooleanField(default=False, help_text='Will not be deleted when the count reaches 0')),
            ],
            options={
                'abstract': False,
                'ordering': ('name',),
            },
            bases=(tagulous.models.models.BaseTagModel, models.Model),
        ),
        migrations.AlterField(
            model_name='document',
            name='file',
            field=models.FileField(max_length=200, upload_to='docs/%Y/%m/%d/', verbose_name='Fichier'),
        ),
        migrations.AlterUniqueTogether(
            name='documenttags',
            unique_together=set([('slug',)]),
        ),
        migrations.AddField(
            model_name='document',
            name='tags',
            field=tagulous.models.fields.TagField(_set_tag_meta=True, autocomplete_view='docs:tags_autocomplete', help_text='Enter a comma-separated tag string', to='docs.DocumentTags'),
        ),
    ]
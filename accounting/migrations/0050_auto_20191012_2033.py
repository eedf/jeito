# Generated by Django 2.1.7 on 2019-10-12 18:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0049_auto_20191012_1455'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='PurchaseInvoice',
            new_name='Purchase',
        ),
    ]
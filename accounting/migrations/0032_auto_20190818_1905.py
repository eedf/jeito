# Generated by Django 2.1.7 on 2019-08-18 17:05

from django.db import migrations


def thirdparty_set_account(apps, schema_editor):
    ThirdParty = apps.get_model('accounting', 'ThirdParty')
    for thirdparty in ThirdParty.objects.all():
        transaction = thirdparty.transaction_set.first()
        thirdparty.account = transaction.account
        if not thirdparty.account:
            print("No account for {}".format(thirdparty))
        thirdparty.save()


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0031_thirdparty_account'),
    ]

    operations = [
        migrations.RunPython(thirdparty_set_account, migrations.RunPython.noop),
    ]

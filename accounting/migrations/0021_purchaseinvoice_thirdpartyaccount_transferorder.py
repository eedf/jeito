# Generated by Django 2.1.7 on 2019-07-10 12:11

from django.db import migrations, models
import django.db.models.deletion
import localflavor.generic.models


def create_purchase_invoices(apps, schema_editor):
    Entry = apps.get_model('accounting', 'Entry')
    PurchaseInvoice = apps.get_model('accounting', 'PurchaseInvoice')
    entries = Entry.objects.filter(date__year=2019) \
        .filter(transaction__account__number__startswith='6') \
        .filter(transaction__account__number__startswith='401')
    for entry in entries:
        purchase_invoice = PurchaseInvoice(entry_ptr=entry)
        purchase_invoice.__dict__.update(entry.__dict__)
        purchase_invoice.save()

def create_third_party_accounts(apps, schema_editor):
    Account = apps.get_model('accounting', 'Account')
    ThirdPartyAccount = apps.get_model('accounting', 'ThirdPartyAccount')
    accounts = Account.objects.filter(number__startswith='4') \
        .exclude(number__startswith='48') \
        .exclude(number__startswith='49')
    for account in accounts:
        third_party_account = ThirdPartyAccount(account_ptr=account)
        third_party_account.__dict__.update(account.__dict__)
        third_party_account.save()


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0020_auto_20190703_0853'),
    ]

    operations = [
        migrations.CreateModel(
            name='PurchaseInvoice',
            fields=[
                ('entry_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='accounting.Entry')),
                ('deadline', models.DateField(blank=True, null=True, verbose_name='Date limite')),
                ('number', models.CharField(blank=True, max_length=100, verbose_name='Numéro')),
            ],
            options={
                'verbose_name': "Facture d'achat",
                'verbose_name_plural': "Factures d'achat",
            },
            bases=('accounting.entry',),
        ),
        migrations.CreateModel(
            name='ThirdPartyAccount',
            fields=[
                ('account_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='accounting.Account')),
                ('iban', localflavor.generic.models.IBANField(blank=True, include_countries=None, max_length=34, use_nordea_extensions=False, verbose_name='IBAN')),
                ('bic', localflavor.generic.models.BICField(blank=True, max_length=11, verbose_name='BIC')),
                ('client_number', models.CharField(blank=True, max_length=100, verbose_name='Numéro client')),
            ],
            options={
                'verbose_name': 'Compte de tiers',
                'verbose_name_plural': 'Comptes de tiers',
                'ordering': ('number',),
            },
            bases=('accounting.account',),
        ),
        migrations.CreateModel(
            name='TransferOrder',
            fields=[
                ('entry_ptr', models.OneToOneField(auto_created=True, on_delete=django.db.models.deletion.CASCADE, parent_link=True, primary_key=True, serialize=False, to='accounting.Entry')),
                ('xml', models.TextField()),
            ],
            options={
                'verbose_name': 'Ordre de virement',
                'verbose_name_plural': 'Ordres de virement',
            },
            bases=('accounting.entry',),
        ),
        migrations.RunPython(
            create_purchase_invoices,
            migrations.RunPython.noop
        ),
        migrations.RunPython(
            create_third_party_accounts,
            migrations.RunPython.noop
        ),
    ]

# Generated by Django 2.2.6 on 2019-10-31 05:09

from django.db import migrations


def create_data(apps, schema_editor):
    Entry = apps.get_model('accounting', 'Entry')
    Income = apps.get_model('accounting', 'Income')
    Expenditure = apps.get_model('accounting', 'Expenditure')
    Cashing = apps.get_model('accounting', 'Cashing')
    entries = Entry.objects.filter(date__year=2019).filter(
        transaction__account__number__startswith='5',
    )
    for entry in entries:
        if entry.transaction_set.filter(account__number__in=('5112000', '5115000', '5170000'), revenue__gt=0).exists():
            cashing = Cashing(entry_ptr=entry)
            cashing.__dict__.update(entry.__dict__)
            cashing.save()
        elif entry.transaction_set.filter(account__number__startswith='5', expense__gt=0).exists():
            income = Income(entry_ptr=entry)
            income.__dict__.update(entry.__dict__)
            income.save()
        else:
            expenditure = Expenditure(entry_ptr=entry)
            expenditure.__dict__.update(entry.__dict__)
            expenditure.save()


class Migration(migrations.Migration):

    dependencies = [
        ('accounting', '0053_cashing_expenditure_income'),
    ]

    operations = [
        migrations.RunPython(create_data, migrations.RunPython.noop),
   ]
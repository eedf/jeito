from django.core.management.base import BaseCommand
from django.db.models import Sum
from ...models import Year, Transaction, Entry, Journal, Account


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('old_year_pk')
        parser.add_argument('new_year_pk')

    def handle(self, *args, **options):
        old_year = Year.objects.get(pk=options['old_year_pk'])
        new_year = Year.objects.get(pk=options['new_year_pk'])
        entry = Entry.objects.create(
            year=new_year,
            date=new_year.start,
            title="A nouveaux",
            journal=Journal.objects.get(number='OD')
        )
        transactions = Transaction.objects.filter(entry__year=old_year, letter=None, account__number__regex='^[125]') \
            .values('account').annotate(balance=Sum('revenue') - Sum('expense'))
        for transaction in transactions:
            Transaction.objects.create(
                entry=entry,
                account=Account.objects.get(pk=transaction['account']),
                expense=max(-transaction['balance'], 0),
                revenue=max(transaction['balance'], 0)
            )
        transactions = Transaction.objects.filter(entry__year=old_year, letter=None, account__number__regex='^4')
        for transaction in transactions:
            Transaction.objects.create(
                entry=entry,
                title=transaction.title,
                account=transaction.account,
                thirdparty=transaction.thirdparty,
                expense=transaction.expense,
                revenue=transaction.revenue
            )
        balance = Transaction.objects.filter(entry__year=old_year, account__number__regex='^[67]') \
            .aggregate(balance=Sum('revenue') - Sum('expense'))['balance']
        account = Account.objects.get(number='1290000' if balance < 0 else '1200000')
        Transaction.objects.create(
            entry=entry,
            title="Résultat de l'exercice {}".format(old_year),
            account=account,
            expense=max(-balance, 0),
            revenue=max(balance, 0)
        )

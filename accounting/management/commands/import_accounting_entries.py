import csv
import datetime
from django.core.management.base import BaseCommand
from ...models import Account, Entry


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('file')

    def handle(self, *args, **options):
        with open(options['file'], 'r') as f:
            reader = csv.reader(f, delimiter=";")
            for row in reader:
                if row[8] != 'G':
                    continue
                if row[2][0] not in ('6', '7'):
                    continue
                date = datetime.date(int(row[1][4:6]), int(row[1][2:4]), int(row[1][0:2]))
                account, created = Account.objects.get_or_create(number=row[2], defaults={'title': row[3]})
                Entry.objects.create(date=date, account=account, title=row[6], amount=row[7])

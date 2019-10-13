from factory import post_generation, LazyFunction, LazyAttributeSequence, Sequence, SubFactory
from factory.django import DjangoModelFactory
from .models import Account, Analytic, Entry, Journal, Purchase, ThirdParty, Transaction, Year


class YearFactory(DjangoModelFactory):
    class Meta:
        model = Year

    title = Sequence(lambda n: "Test year {:03d}".format(n))
    start = '2010-05-13'
    end = '2011-05-12'


class AccountFactory(DjangoModelFactory):
    class Meta:
        model = Account

    class Params:
        prefix = 0

    number = LazyAttributeSequence(lambda o, n: "{:07d}".format(o.prefix + n))
    title = LazyAttributeSequence(lambda o, n: "Test account {:03d}".format(o.prefix + n))


class AnalyticFactory(DjangoModelFactory):
    class Meta:
        model = Analytic

    number = Sequence(lambda n: "{:03d}".format(n))
    title = Sequence(lambda n: "Test analytic {:03d}".format(n))


class ThirdPartyFactory(DjangoModelFactory):
    class Meta:
        model = ThirdParty

    number = Sequence(lambda n: "X{:03d}".format(n))
    title = Sequence(lambda n: "Test third party {:03d}".format(n))
    account = SubFactory(AccountFactory)
    type = 0


class EntryFactory(DjangoModelFactory):
    class Meta:
        model = Entry

    title = Sequence(lambda n: "Test entry {:03d}".format(n))
    journal = LazyFunction(lambda: Journal.objects.get(number='OD'))
    year = SubFactory(YearFactory)


class PurchaseFactory(EntryFactory):
    class Meta:
        model = Purchase

    title = Sequence(lambda n: "Test purchase {:03d}".format(n))
    journal = LazyFunction(lambda: Journal.objects.get(number='HA'))

    @post_generation
    def transaction_set(self, create, extracted, **kwargs):
        self.transaction_set.add(TransactionFactory(entry=self, account__prefix=6000000))
        self.transaction_set.add(TransactionFactory(entry=self, account__prefix=4010000))


class TransactionFactory(DjangoModelFactory):
    class Meta:
        model = Transaction

    entry = SubFactory(EntryFactory)
    account = SubFactory(AccountFactory)

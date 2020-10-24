import datetime
import fintech
fintech.register()  # noqa
from fintech import sepa
from django.conf import settings
from django.db import models
from django.db.models.functions import Coalesce
from django.urls import reverse
from localflavor.generic.models import IBANField, BICField


class Year(models.Model):
    title = models.CharField(verbose_name="Intitulé", max_length=100)
    start = models.DateField(verbose_name="Début")
    end = models.DateField(verbose_name="Fin")
    opened = models.BooleanField(verbose_name="Ouvert", default=False)

    class Meta:
        verbose_name = "Exercice"
        ordering = ('start', 'end')

    def __str__(self):
        return self.title


class Journal(models.Model):
    number = models.CharField(verbose_name="Numéro", max_length=2, unique=True)
    title = models.CharField(verbose_name="Intitulé", max_length=100)

    class Meta:
        verbose_name = "Journal"
        ordering = ('number', )

    def __str__(self):
        return "{} : {}".format(self.number, self.title)


class Account(models.Model):
    number = models.CharField(verbose_name="Numéro", max_length=7, unique=True)
    title = models.CharField(verbose_name="Intitulé", max_length=100)

    class Meta:
        verbose_name = "Compte"
        ordering = ('number', )

    def __str__(self):
        return "{} : {}".format(self.number, self.title)


class ThirdParty(models.Model):
    TYPE_CHOICES = (
        (0, "Client"),
        (1, "Fournisseur"),
        (2, "Salarié"),
        (3, "Autre"),
    )

    number = models.CharField(verbose_name="Numéro", max_length=4, unique=True)
    title = models.CharField(verbose_name="Intitulé", max_length=100)
    iban = IBANField(verbose_name="IBAN", blank=True)
    bic = BICField(verbose_name="BIC", blank=True)
    client_number = models.CharField(verbose_name="Numéro client", max_length=100, blank=True)
    account = models.ForeignKey(Account, verbose_name="Compte principal", on_delete=models.PROTECT)
    type = models.IntegerField(verbose_name="Type", choices=TYPE_CHOICES)

    class Meta:
        verbose_name = "Tiers"
        verbose_name_plural = "Tiers"
        ordering = ('number', )

    def __str__(self):
        return "{} : {}".format(self.number, self.title)

    @property
    def account_number(self):
        return self.account.number


class Analytic(models.Model):
    number = models.CharField(verbose_name="Numéro", max_length=3, unique=True)
    title = models.CharField(verbose_name="Intitulé", max_length=100)

    class Meta:
        verbose_name = "Analytique"
        ordering = ('number', )

    def __str__(self):
        return "{} : {}".format(self.number, self.title)


class EntryManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.annotate(
            revenue=Coalesce(models.Sum('transaction__revenue'), 0),
            expense=Coalesce(models.Sum('transaction__expense'), 0),
            balance=Coalesce(models.Sum('transaction__revenue') - models.Sum('transaction__expense'), 0)
        )
        return qs


class Entry(models.Model):
    year = models.ForeignKey(Year, verbose_name="Exercice", on_delete=models.PROTECT)
    date = models.DateField(verbose_name="Date", default=datetime.date.today)
    journal = models.ForeignKey(Journal, verbose_name="Journal", on_delete=models.PROTECT)
    title = models.CharField(verbose_name="Intitulé", max_length=100)
    scan = models.FileField(verbose_name="Justificatif", upload_to='justificatif', blank=True)
    exported = models.BooleanField(verbose_name="Exporté", default=False)

    objects = EntryManager()

    class Meta:
        verbose_name = "Écriture"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('accounting:entry', kwargs={'pk': self.pk})

    def balanced(self):
        return self.balance == 0
    balanced.short_description = "Équilibré"
    balanced.boolean = True

    def delete(self, *args, **kwargs):
        "Delete lettering if need be"
        Letter.objects.filter(transaction__entry=self).delete()
        return super().delete(*args, **kwargs)


class Purchase(Entry):
    deadline = models.DateField(verbose_name="Date limite", null=True, blank=True)
    number = models.CharField(verbose_name="Numéro", max_length=100, blank=True)

    objects = EntryManager()

    class Meta:
        verbose_name = "Facture fournisseur"
        verbose_name_plural = "Factures fournisseur"


class Sale(Entry):
    number = models.CharField(verbose_name="Numéro", max_length=100, blank=True)

    objects = EntryManager()

    class Meta:
        verbose_name = "Facture client"
        verbose_name_plural = "Factures client"


class Income(Entry):
    objects = EntryManager()
    METHOD_CHOICES = (
        ('5112000', "Chèque"),
        ('5115000', "ANCV"),
        ('5120000', "Virement"),
        ('5170000', "Carte"),
        ('5300000', "Espèces"),
    )

    class Meta:
        verbose_name = "Recette"
        verbose_name_plural = "Recettes"

    @property
    def client_transaction(self):
        try:
            return self.transaction_set.get(account__number__startswith='4')
        except Transaction.DoesNotExist:
            return None

    @property
    def cash_transaction(self):
        try:
            return self.transaction_set.get(account__number__startswith='5')
        except Transaction.DoesNotExist:
            return None

    @property
    def deposit(self):
        if not self.client_transaction:
            return None
        return self.client_transaction.account.number == '4190000'

    @property
    def method(self):
        if not self.cash_transaction:
            return None
        return dict(self.METHOD_CHOICES)[self.cash_transaction.account.number]


class Expenditure(Entry):
    METHOD_CHOICES = (
        (1, "Carte bancaire"),
        (2, "Chèque"),
        (3, "Espèces"),
        (4, "Prélèvement"),
        (5, "Virement"),
    )

    method = models.IntegerField(choices=METHOD_CHOICES)

    objects = EntryManager()

    class Meta:
        verbose_name = "Dépense"
        verbose_name_plural = "Dépenses"

    @property
    def provider_transactions(self):
        return self.transaction_set.filter(account__number__startswith='4')

    @property
    def cash_transaction(self):
        try:
            return self.transaction_set.get(account__number__startswith='5')
        except Transaction.DoesNotExist:
            return None

    def sepa(self):
        # Create the debtor account from an IBAN
        debtor = sepa.Account(settings.IBAN, settings.HOLDER)
        # Create a SEPACreditTransfer instance
        sct = sepa.SEPACreditTransfer(debtor)
        for transaction in self.transaction_set.filter(expense__gt=0):
            thirdparty = transaction.thirdparty
            if not thirdparty:
                raise Exception("No third party for {}".format(transaction))
            # Create the creditor account from a tuple (IBAN, BIC)
            try:
                creditor = sepa.Account(thirdparty.iban, thirdparty.title)
            except ValueError as e:
                raise Exception("{} for thirdparty {}".format(e, thirdparty))
            # Add the transaction
            sct.add_transaction(
                creditor,
                sepa.Amount(transaction.expense, 'EUR'),
                transaction.title
            )
        return sct.render().decode('ascii')


class Cashing(Entry):
    objects = EntryManager()

    class Meta:
        verbose_name = "Encaissement"
        verbose_name_plural = "Encaissements"


class Letter(models.Model):
    def __str__(self):
        i = self.id - 1
        s = ''
        while i:
            s = chr((i % 26) + 65) + s
            i //= 26
        return s


class Transaction(models.Model):
    entry = models.ForeignKey(Entry, on_delete=models.CASCADE)
    title = models.CharField(verbose_name="Intitulé", max_length=100, blank=True)
    account = models.ForeignKey(Account, verbose_name="Compte", on_delete=models.PROTECT)
    thirdparty = models.ForeignKey(ThirdParty, verbose_name="Tiers", null=True, blank=True,
                                   on_delete=models.PROTECT)
    analytic = models.ForeignKey(Analytic, verbose_name="Analytique", blank=True, null=True, on_delete=models.PROTECT)
    expense = models.DecimalField(verbose_name="Débit", max_digits=8, decimal_places=2, default=0)
    revenue = models.DecimalField(verbose_name="Crédit", max_digits=8, decimal_places=2, default=0)
    reconciliation = models.DateField(verbose_name="Rapprochement", blank=True, null=True)
    letter = models.ForeignKey(Letter, verbose_name="Lettrage", blank=True, null=True, on_delete=models.SET_NULL)

    def __str__(self):
        return self.title or self.entry.title

    def date(self):
        return self.entry.date
    date.short_description = "Date"
    date.admin_order_field = "entry__date"

    @property
    def date_dmy(self):
        return self.date().strftime('%d%m%y')

    @property
    def balance(self):
        return self.revenue - self.expense

    @property
    def account_number(self):
        return self.account.number

    @property
    def thirdparty_number(self):
        return self.thirdparty and self.thirdparty.number

    @property
    def journal_number(self):
        return self.entry.journal.number

    @property
    def full_title(self):
        return str(self)

    def save(self, *args, **kwargs):
        "Delete lettering if need be"
        if self.id and self.letter:
            try:
                old = Transaction.objects.get(id=self.id)
            except Transaction.DoesNotExist:
                old = None
            if old and self.expense != old.expense or self.revenue != old.revenue:
                self.letter.delete()
                self.letter = None
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        "Delete lettering if need be"
        if self.letter:
            self.letter.delete()
        return super().delete(*args, **kwargs)


class BankStatement(models.Model):
    year = models.ForeignKey(Year, verbose_name="Exercice", on_delete=models.PROTECT)
    date = models.DateField()
    number = models.PositiveIntegerField(verbose_name="Numéro", blank=True, null=True)
    scan = models.FileField(upload_to='releves')
    balance = models.DecimalField(verbose_name="Solde", max_digits=8, decimal_places=2)

    class Meta:
        verbose_name = "Relevé de compte"
        verbose_name_plural = "Relevés de compte"
        ordering = ('-date', )

    @property
    def entries_balance(self):
        transactions = Transaction.objects \
            .filter(account__number='5120000') \
            .filter(reconciliation__lte=self.date)
        sums = transactions.aggregate(expense=models.Sum('expense'), revenue=models.Sum('revenue'))
        return sums['expense'] - sums['revenue']

    @property
    def reconciliation(self):
        return self.balance - self.entries_balance

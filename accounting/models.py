import datetime
import fintech
fintech.register()  # noqa
from fintech import sepa
from django.conf import settings
from django.db import models
from django.urls import reverse
from localflavor.generic.models import IBANField, BICField


class Journal(models.Model):
    number = models.CharField(verbose_name="Numéro", max_length=2)
    title = models.CharField(verbose_name="Intitulé", max_length=100)

    class Meta:
        verbose_name = "Journal"
        ordering = ('number', )

    def __str__(self):
        return "{} : {}".format(self.number, self.title)


class Account(models.Model):
    number = models.CharField(verbose_name="Numéro", max_length=7)
    title = models.CharField(verbose_name="Intitulé", max_length=100)

    class Meta:
        verbose_name = "Compte"
        ordering = ('number', )

    def __str__(self):
        return "{} : {}".format(self.number, self.title)


class ThirdParty(models.Model):
    number = models.CharField(verbose_name="Numéro", max_length=4)
    title = models.CharField(verbose_name="Intitulé", max_length=100)
    iban = IBANField(verbose_name="IBAN", blank=True)
    bic = BICField(verbose_name="BIC", blank=True)
    client_number = models.CharField(verbose_name="Numéro client", max_length=100, blank=True)

    class Meta:
        verbose_name = "Tiers"
        verbose_name_plural = "Tiers"
        ordering = ('number', )

    def __str__(self):
        return "{} : {}".format(self.number, self.title)


class Analytic(models.Model):
    number = models.CharField(verbose_name="Numéro", max_length=3)
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
            revenue=models.Sum('transaction__revenue'),
            expense=models.Sum('transaction__expense'),
            balance=models.Sum('transaction__revenue') - models.Sum('transaction__expense')
        )
        return qs


class Entry(models.Model):
    date = models.DateField(verbose_name="Date", default=datetime.date.today)
    journal = models.ForeignKey(Journal, verbose_name="Journal", on_delete=models.PROTECT)
    title = models.CharField(verbose_name="Intitulé", max_length=100)
    scan = models.FileField(verbose_name="Justificatif", upload_to='justificatif', blank=True)
    forwarded = models.BooleanField(verbose_name="Envoyé à la compta", default=False)
    entered = models.BooleanField(verbose_name="Saisi dans la compta", default=False)
    projected = models.BooleanField(verbose_name="Prévisionnel", default=False)

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


class PurchaseInvoice(Entry):
    deadline = models.DateField(verbose_name="Date limite", null=True, blank=True)
    number = models.CharField(verbose_name="Numéro", max_length=100, blank=True)

    class Meta:
        verbose_name = "Facture d'achat"
        verbose_name_plural = "Factures d'achat"


class TransferOrder(Entry):
    xml = models.TextField(editable=False)

    class Meta:
        verbose_name = "Ordre de virement"
        verbose_name_plural = "Ordres de virement"

    def save(self, *args, **kwargs):
        # Create the debtor account from an IBAN
        debtor = sepa.Account(settings.IBAN, settings.HOLDER)
        # Create a SEPACreditTransfer instance
        sct = sepa.SEPACreditTransfer(debtor)
        for transaction in self.transaction_set.filter(expense__gt=0):
            thirdparty = transaction.thirdparty
            if not thirdparty:
                self.xml = "No third party for {}".format(transaction)
                super().save(*args, **kwargs)
                return
            # Create the creditor account from a tuple (IBAN, BIC)
            try:
                creditor = sepa.Account(thirdparty.iban, thirdparty.title)
            except ValueError as e:
                self.xml = "{} for thirdparty {}".format(e, thirdparty)
                super().save(*args, **kwargs)
                return
            # Add the transaction
            sct.add_transaction(
                creditor,
                sepa.Amount(transaction.expense, 'EUR'),
                transaction.title
            )
        self.xml = sct.render().decode('ascii')
        super().save(*args, **kwargs)


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

    def __str__(self):
        return self.title or self.entry.title

    def date(self):
        return self.entry.date
    date.short_description = "Date"
    date.admin_order_field = "entry__date"

    @property
    def balance(self):
        return self.revenue - self.expense


class BankStatement(models.Model):
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
        transactions = Transaction.objects.filter(account__number='5120000', reconciliation__lte=self.date)
        sums = transactions.aggregate(expense=models.Sum('expense'), revenue=models.Sum('revenue'))
        return sums['expense'] - sums['revenue']

    @property
    def reconciliation(self):
        return self.balance - self.entries_balance

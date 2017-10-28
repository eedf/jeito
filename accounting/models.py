from django.db import models
from django.urls import reverse


class Account(models.Model):
    number = models.CharField(verbose_name="Numéro", max_length=7)
    title = models.CharField(verbose_name="Intitulé", max_length=100)

    class Meta:
        verbose_name = "Compte"
        ordering = ('number', )

    def __str__(self):
        return "{} {}".format(self.number, self.title)


class Analytic(models.Model):
    title = models.CharField(verbose_name="Intitulé", max_length=100)

    class Meta:
        verbose_name = "Analytique"
        ordering = ('title', )

    def __str__(self):
        return self.title


class Entry(models.Model):
    date = models.DateField(verbose_name="Date")
    title = models.CharField(verbose_name="Intitulé", max_length=100)
    scan = models.FileField(upload_to='justificatif', blank=True)
    forwarded = models.BooleanField(verbose_name="Envoyé à la compta", default=False)
    entered = models.BooleanField(verbose_name="Saisi dans la compta", default=False)
    projected = models.BooleanField(verbose_name="Prévisionnel", default=False)

    class Meta:
        verbose_name = "Écriture"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('accounting:entry', kwargs={'pk': self.pk})

    def revenue(self):
        return sum([t.revenue for t in self.transaction_set.all()])

    def expense(self):
        return sum([t.expense for t in self.transaction_set.all()])

    def balanced(self):
        return sum([t.revenue - t.expense for t in self.transaction_set.all()]) == 0
    balanced.short_description = "Équilibré"
    balanced.boolean = True


class Transaction(models.Model):
    entry = models.ForeignKey(Entry)
    title = models.CharField(verbose_name="Intitulé", max_length=100, blank=True)
    account = models.ForeignKey(Account, verbose_name="Compte")
    analytic = models.ForeignKey(Analytic, verbose_name="Analytique", blank=True, null=True)
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

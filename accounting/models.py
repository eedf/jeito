from django.db import models


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

    class Meta:
        verbose_name = "Écriture"

    def __str__(self):
        return self.title

    def balanced(self):
        return sum([t.revenue - t.expense for t in self.transaction_set.all()]) == 0
    balanced.short_description = "Équilibré"
    balanced.boolean = True


class Transaction(models.Model):
    entry = models.ForeignKey(Entry)
    title = models.CharField(verbose_name="Intitulé", max_length=100, blank=True)
    account = models.ForeignKey(Account, verbose_name="Compte")
    analytic = models.ForeignKey(Analytic, verbose_name="Analytique", blank=True, null=True)
    revenue = models.DecimalField(verbose_name="Recette", max_digits=8, decimal_places=2, default=0)
    expense = models.DecimalField(verbose_name="Dépense", max_digits=8, decimal_places=2, default=0)

    def __str__(self):
        return self.title or self.entry.title

    def date(self):
        return self.entry.date
    date.short_description = "Date"
    date.admin_order_field = "entry__date"


class Budget(models.Model):
    analytic = models.OneToOneField(Analytic, verbose_name="Analytique")
    amount = models.DecimalField(verbose_name="Montant", max_digits=8, decimal_places=2)
    comment = models.CharField(verbose_name="Commentaire", max_length=1000, blank=True)

    def done(self):
        qs = self.analytic.entry_set.aggregate(amount=models.Sum(models.F('revenue') - models.F('expense')))
        return qs['amount'] or 0

    def diff(self):
        return self.amount - self.done()


class BankStatement(models.Model):
    date = models.DateField()
    scan = models.FileField(upload_to='releves')
    balance = models.DecimalField(verbose_name="Solde", max_digits=8, decimal_places=2)

    class Meta:
        verbose_name = "Relevé de compte"
        verbose_name_plural = "Relevés de compte"
        ordering = ('-date', )

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
    account = models.ForeignKey(Account, verbose_name="Compte")
    title = models.CharField(verbose_name="Intitulé", max_length=100)
    revenue = models.DecimalField(verbose_name="Recette", max_digits=8, decimal_places=2)
    expense = models.DecimalField(verbose_name="Dépense", max_digits=8, decimal_places=2)
    analytic = models.ForeignKey(Analytic, verbose_name="Analytique", blank=True, null=True)
    scan = models.FileField(upload_to='justificatif', blank=True)

    class Meta:
        verbose_name = "Écriture"

    def __str__(self):
        return self.title


class Budget(models.Model):
    analytic = models.OneToOneField(Analytic, verbose_name="Analytique")
    amount = models.DecimalField(verbose_name="Montant", max_digits=8, decimal_places=2)
    comment = models.CharField(verbose_name="Commentaire", max_length=1000, blank=True)

    def done(self):
        qs = self.analytic.entry_set.aggregate(amount=models.Sum(models.F('revenue') - models.F('expense')))
        return qs['amount']

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

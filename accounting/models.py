from django.db import models


class Account(models.Model):
    number = models.CharField(verbose_name="Numéro", max_length=7)
    title = models.CharField(verbose_name="Intitulé", max_length=100)

    class Meta:
        verbose_name = "Compte"

    def __str__(self):
        return "{} {}".format(self.number, self.title)


class Analytic(models.Model):
    title = models.CharField(verbose_name="Intitulé", max_length=100)

    class Meta:
        verbose_name = "Analytique"

    def __str__(self):
        return self.title


class Entry(models.Model):
    date = models.DateField(verbose_name="Date")
    account = models.ForeignKey(Account, verbose_name="Compte")
    title = models.CharField(verbose_name="Intitulé", max_length=100)
    amount = models.DecimalField(verbose_name="Montant", max_digits=8, decimal_places=2)
    analytic = models.ForeignKey(Analytic, verbose_name="Analytique", blank=True, null=True)

    class Meta:
        verbose_name = "Écriture"

    def __str__(self):
        return self.title

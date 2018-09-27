from django.db import models
from members.models import Structure, Person


class Membership(models.Model):
    person = models.ForeignKey(Person)
    report = models.ForeignKey('Report')
    function = models.TextField(max_length=100, blank=True)


class Report(models.Model):
    structure = models.ForeignKey(Structure, verbose_name='SLA', on_delete=models.PROTECT)
    date = models.DateField("Date", null=True, blank=True)
    location = models.CharField("Lieu", max_length=100, blank=True)
    nb_presents = models.IntegerField("Nombre de personnes présentes", null=True, blank=True)
    nb_voters = models.IntegerField("Nombre de votants", null=True, blank=True)
    representative = models.ForeignKey(
        Person, verbose_name="Représentant", on_delete=models.PROTECT, null=True,
        related_name="report_representative_set")
    favour = models.PositiveIntegerField("Pour", null=True, blank=True)
    against = models.PositiveIntegerField("Contre", null=True, blank=True)
    abstention = models.PositiveIntegerField("Abstention", null=True, blank=True)
    balance = models.DecimalField(
        'Résultat exercice en cours', decimal_places=2, max_digits=9, null=True, blank=True)
    budget = models.NullBooleanField("Présentation d'un budget prévisionnel", null=True, blank=True)
    delegate = models.ForeignKey(
        Person, verbose_name="Délégué élu", on_delete=models.PROTECT, null=True, blank=True,
        related_name="report_delegate_set")
    alternate = models.ForeignKey(
        Person, verbose_name="Délégué suppléant élu", on_delete=models.PROTECT,
        null=True, blank=True, related_name="report_alternate_set")
    responsible = models.ForeignKey(
        Person, verbose_name="Responsable", on_delete=models.PROTECT, null=True, blank=True,
        related_name='report_responsible_set')
    treasurer = models.ForeignKey(
        Person, verbose_name="Trésorier", on_delete=models.PROTECT, null=True, blank=True,
        related_name='report_treasurer_set')
    responsible_validation = models.NullBooleanField(
        "Signature du responsable de la SLA", null=True, blank=True)
    representative_validation = models.NullBooleanField(
        "Signature du représentant", null=True, blank=True)
    comments_activity_report = models.TextField(
        "Commentaires concernant le temps rapport d'activité", blank=True)
    comments_finances = models.TextField(
        "Commentaires concernant le point financier", blank=True)
    comments_national = models.TextField(
        "Commentaires concernant les sujets d'intérêts nationaux abordés", blank=True)
    comments_regional = models.TextField(
        "Commentaires concernant les sujets d'intérêts régionaux abordés", blank=True)
    comments_problems = models.TextField(
        "Problèmes/difficultés survenus dans la tenue de la réunion", blank=True)
    team = models.ManyToManyField(Person, through=Membership)

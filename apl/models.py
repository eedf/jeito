from django.db import models
from django.urls import reverse
from members.models import Structure, Person


class Report(models.Model):
    season = models.IntegerField(verbose_name="Saison",
                                 choices=[(s, "{}/{}".format(s - 1, s)) for s in range(2017, 2018)])
    structure = models.ForeignKey(Structure, verbose_name="Structure")
    location = models.CharField(verbose_name="Lieu", max_length=100, blank=True)
    date = models.DateField(verbose_name="Date", blank=True, null=True)
    representative = models.CharField(verbose_name="Représentant de l'échelon régional/national", max_length=100,
                                      blank=True)
    headcount = models.IntegerField(verbose_name="Effectif présents", null=True, blank=True)
    voters = models.IntegerField(verbose_name="Nombre de votants", null=True, blank=True)
    # Activity report
    favour = models.IntegerField(verbose_name="Pour", null=True, blank=True)
    against = models.IntegerField(verbose_name="Contre", null=True, blank=True)
    absention = models.IntegerField(verbose_name="Abstention", null=True, blank=True)
    # Financial report
    result = models.IntegerField(verbose_name="Résultat de l'exercice en cours", null=True, blank=True)
    budget = models.NullBooleanField(verbose_name="Présentation d'un budget prévisionnel", null=True, blank=True)
    # Delegate AG
    delegate = models.ForeignKey(Person, verbose_name="Délégué élu", null=True, blank=True, related_name='delegate_set')
    delegate_votes = models.IntegerField(verbose_name="Voix obtenues", null=True, blank=True)
    alternate = models.ForeignKey(Person, verbose_name="Délégué suppléant élu", null=True, blank=True,
                                  related_name='alternate_set')
    alternate_votes = models.IntegerField(verbose_name="Voix obtenues", null=True, blank=True)
    # Team
    leader = models.ForeignKey(Person, verbose_name="Responsable", null=True, blank=True, related_name='leader_set')
    leader_votes = models.IntegerField(verbose_name="Voix obtenues", null=True, blank=True)
    treasurer = models.ForeignKey(Person, verbose_name="Trésorier", null=True, blank=True, related_name='treasurer_set')
    treasurer_votes = models.IntegerField(verbose_name="Voix obtenues", null=True, blank=True)
    activity_comments = models.TextField(verbose_name="Commentaires concernant le temps rapport d'activité", blank=True)
    financial_comments = models.TextField(verbose_name="Commentaires concernant le point financier", blank=True)
    national_comments = models.TextField(verbose_name="Commentaires concernant les sujets d’intérêts nationaux abordés",
                                         blank=True)
    regional_comments = models.TextField(verbose_name="Commentaires concernant les sujets d’intérêts régionaux abordés",
                                         blank=True)
    problems = models.TextField(verbose_name="Problèmes/difficultés survenus dans la tenue de la réunion", blank=True)
    scan = models.FileField(verbose_name="Scan du PV papier", blank=True)

    def get_absolute_url(self):
        return reverse('apl:report_detail', kwargs={'pk': self.pk})


class TeamMember(models.Model):
    report = models.ForeignKey(Report)
    person = models.ForeignKey(Person, verbose_name="Membre")
    function = models.CharField(verbose_name="Fonction", max_length=100, blank=True)

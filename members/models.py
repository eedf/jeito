from django.db import models
from django.db.models import Q
from django.conf import settings
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import RegexValidator

from oauth2client.contrib.django_util.models import CredentialsField
from mptt.models import MPTTModel, TreeForeignKey, TreeManager

from .utils import current_season


class PersonManager(BaseUserManager):
    def create_user(self, password=None, **kwargs):
        user = self.model(**kwargs)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, **kwargs):
        return self.create_user(is_superuser=True, **kwargs)


class StructureQuerySet(models.QuerySet):
    def for_user(self, user):
        if user.is_superuser:
            return self
        return self.filter(nomination__adhesion__person=user,
                           nomination__adhesion__season=current_season())

    def centers(self):
        return self.filter(Q(type=15) | Q(type__in=(10, 11), subtype=1))


class Structure(MPTTModel):
    TYPE_CHOICES = (
        (1, "Cercle"),
        (2, "Clan Ainé"),
        (3, "Comité directeur"),
        (4, "Département"),
        (5, "Pôle"),
        (6, "Région"),
        (7, "Ronde"),
        (8, "Siège"),
        (9, "Sommet"),
        (10, "Structure locale d'activité"),
        (11, "Structure locale rattachée"),
        (12, "Unité Défi"),
        (13, "Unité Eclé"),
        (14, "Unité Nomade"),
        (15, "Centre permanent national"),
    )
    SUBTYPE_CHOICES = (
        (1, "Centre et terrain"),
        (2, "Groupe local"),
        (3, "Ludotheque"),
        (4, "Service vacances"),
    )

    number = models.CharField(
        "Numéro", max_length=10, unique=True,
        validators=[
            RegexValidator('\d{10}', message="Le numéro de structure comporte 10 chiffres")
        ]
    )
    name = models.CharField("Nom", max_length=100)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)
    type = models.IntegerField("Type", choices=TYPE_CHOICES)
    subtype = models.IntegerField("Sous-type", choices=SUBTYPE_CHOICES, null=True, blank=True)
    google = CredentialsField(null=True, blank=True)

    objects = TreeManager.from_queryset(StructureQuerySet)()

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Structure"

    class MPTTMeta:
        order_insertion_by = ['name']

    def nominated(self, person, season=None):
        if person.is_superuser:
            return True
        nominations = Nomination.objects.filter(adhesion__season=season or current_season())
        nominations = nominations.filter(adhesion__person=person)
        nominations = nominations.filter(structure=self)
        return nominations.exists()


class Function(models.Model):
    CATEGORY_CHOICES = (
        (0, "Jeune/Participant"),
        (1, "Responsable"),
        (2, "Cadre bénévole"),
        (3, "Stagiaire"),
        (4, "Parent/Ami"),
        (5, "Salarié/SC"),
    )

    code = models.CharField("Code", max_length=5)
    season = models.IntegerField()
    name_m = models.CharField("Nom masculin", max_length=100)
    name_f = models.CharField("Nom féminin", max_length=100)
    category = models.IntegerField("Categorie", choices=CATEGORY_CHOICES, null=True, blank=True)

    def __str__(self):
        return "{} {}".format(self.season, self.name_m)

    class Meta:
        verbose_name = "Fonction"
        unique_together = ('code', 'season')


class Rate(models.Model):
    CATEGORY_CHOICES = (
        (1, 'Enfant'),
        (2, 'Responsable'),
        (3, 'Soutien'),
        (4, 'Stagiaire'),
        (5, 'Import SV/CP'),
        (6, 'Découverte'),
        (7, 'Salarié'),
    )

    name = models.CharField("Nom", max_length=256)
    season = models.IntegerField()
    rate = models.DecimalField("Tarif", max_digits=5, decimal_places=2, null=True, blank=True)
    rate_after_tax_ex = models.DecimalField(
        "Tarif après défiscalisation", max_digits=5, decimal_places=2,
        null=True, blank=True)
    bracket = models.CharField("Tranche", max_length=100, blank=True)
    category = models.IntegerField("Catégorie", choices=CATEGORY_CHOICES, null=True, blank=True)

    def __str__(self):
        return "{} {}".format(self.season, self.name)

    class Meta:
        verbose_name = "Tarif"
        unique_together = ('name', 'season')


class Person(PermissionsMixin, AbstractBaseUser):
    GENDER_MALE = 1
    GENDER_FEMALE = 2
    GENDER_CHOICES = (
        (GENDER_MALE, "Masculin"),
        (GENDER_FEMALE, "Féminin"),
    )

    number = models.CharField(
        u'Numéro', max_length=6, unique=True,
        validators=[
            RegexValidator('\d{6}', message="Le numéro d'adhérent comporte 6 chiffres")
        ]
    )
    first_name = models.CharField(u'Prénom', max_length=100, blank=True)
    last_name = models.CharField(u'Nom', max_length=100, blank=True)
    email = models.EmailField(u'Email', blank=True)
    gender = models.IntegerField("Genre", blank=True, null=True, choices=GENDER_CHOICES)
    birthdate = models.DateField("Date de naissance", blank=True, null=True)

    USERNAME_FIELD = 'number'
    objects = PersonManager()

    class Meta:
        verbose_name = "Personne"

    def __str__(self):
        return self.number

    def get_short_name(self):
        return u'{first_name}'.format(**self.__dict__)

    def get_full_name(self):
        return u'{first_name} {last_name}'.format(**self.__dict__)

    @property
    def is_staff(self):
        return self.is_superuser

    @property
    def adhesion(self):
        today = settings.NOW()
        if today.month < 9:
            seasons = (today.year, )
        elif today.month == 9:
            seasons = (today.year, today.year + 1)
        else:
            seasons = (today.year + 1, )
        try:
            return self.adhesions.filter(season__in=seasons).latest('season')
        except Adhesion.DoesNotExist:
            return None

    @property
    def is_active(self):
        if self.is_superuser:
            return True
        return self.adhesion is not None

    @property
    def is_becours(self):
        if self.is_superuser:
            return True
        return self.adhesion and self.adhesion.nomination_set.filter(structure__number='2700000500').exists()


class Adhesion(models.Model):
    person = models.ForeignKey(Person, related_name='adhesions')
    season = models.IntegerField("Saison")
    date = models.DateField()
    rate = models.ForeignKey(Rate, verbose_name="Tarif")
    structure = models.ForeignKey(Structure, verbose_name="Structure", related_name='adherents')

    def __str__(self):
        return "{self.season}-{self.person}".format(self=self)


class Nomination(models.Model):
    adhesion = models.ForeignKey(Adhesion, verbose_name="Adhésion")
    structure = models.ForeignKey(Structure, verbose_name="Structure")
    function = models.ForeignKey(Function, verbose_name="Fonction")
    main = models.BooleanField(verbose_name="Principale", default=False)

    class Meta:
        unique_together = ('adhesion', 'structure', 'function')

    def __str__(self):
        return "{self.adhesion}:{self.function}@{self.structure}".format(self=self)

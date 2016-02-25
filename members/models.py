from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.core.validators import RegexValidator
from django.utils.timezone import now

from mptt.models import MPTTModel, TreeForeignKey


class PersonManager(BaseUserManager):
    def create_user(self, password=None, **kwargs):
        user = self.model(**kwargs)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, **kwargs):
        return self.create_user(is_superuser=True, **kwargs)


class Structure(MPTTModel):
    number = models.CharField(
        "Numéro", max_length=10, unique=True,
        validators=[
            RegexValidator('\d{10}', message="Le numéro de structure comporte 10 chiffres")
        ]
    )
    name = models.CharField("Nom", max_length=100)
    parent = TreeForeignKey('self', null=True, blank=True, related_name='children', db_index=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Structure"

    class MPTTMeta:
        order_insertion_by = ['name']


class Function(models.Model):
    code = models.CharField("Code", max_length=5)
    season = models.IntegerField()
    name_m = models.CharField("Nom masculin", max_length=100)
    name_f = models.CharField("Nom féminin", max_length=100)

    def __str__(self):
        return self.name_m

    class Meta:
        verbose_name = "Fonction"
        unique_together = ('code', 'season')


class Rate(models.Model):
    CATEGORY_CHOICES = (
        (1, 'Enfants'),
        (2, 'Cadres'),
        (3, 'Amis'),
        (4, 'Stagiaires'),
        (5, 'Services Vacances'),
        (6, 'Découverte'),
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
        return self.name

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

    USERNAME_FIELD = 'number'
    objects = PersonManager()

    class Meta:
        verbose_name = "Personne"

    def get_short_name(self):
        return u'{first_name}'.format(**self.__dict__)

    def get_full_name(self):
        return u'{first_name} {last_name}'.format(**self.__dict__)

    @property
    def is_staff(self):
        return self.is_superuser

    @property
    def is_active(self):
        today = now()
        if today.month < 9:
            seasons = [today.year]
        elif today.mont == 9:
            seasons = [today.year, today.year + 1]
        else:
            seasons = [today.year + 1]
        return self.adhesions.filter(season__in=seasons).exists()


class Adhesion(models.Model):
    person = models.ForeignKey(Person, related_name='adhesions')
    season = models.IntegerField("Saison")
    date = models.DateField()
    rate = models.ForeignKey(Rate, verbose_name="Tarif")
    structure = models.ForeignKey(Structure, verbose_name="Structure", related_name='adherents')
    function = models.ForeignKey(Function, verbose_name="Fonction")

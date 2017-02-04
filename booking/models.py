from cuser.middleware import CuserMiddleware
from decimal import Decimal
from django.db import models
from django.db.models import Case, ExpressionWrapper, F, Min, Max, Sum, Value, When
from django.db.models.functions import Coalesce, ExtractDay
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils.timezone import now
from math import floor


class TrackingEvent(models.Model):
    ADD = 1
    CHANGE = 2
    DELETE = 3
    OPERATION_CHOICES = (
        (ADD, "Ajout"),
        (CHANGE, "Modification"),
        (DELETE, "Suppression"),
    )
    operation = models.IntegerField(verbose_name="Opération", choices=OPERATION_CHOICES)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, verbose_name="Utilisateur", blank=True, null=True,
                             related_name="tracking_events", on_delete=models.PROTECT)
    date = models.DateTimeField()
    obj_ct = models.ForeignKey(ContentType, related_name='log_entries', on_delete=models.PROTECT)
    obj_pk = models.PositiveIntegerField()
    obj = GenericForeignKey('obj_ct', 'obj_pk')

    class Meta:
        verbose_name = "Événement"


class TrackingValue(models.Model):
    event = models.ForeignKey(TrackingEvent, verbose_name="Événement")
    field = models.CharField(max_length=100, verbose_name="Champ")
    value = models.TextField(null=True, verbose_name="Valeur")

    class Meta:
        verbose_name = "Valeur"


class TrackingMixin(object):
    def save(self, *args, **kwargs):
        change = bool(self.pk)
        if change:
            old = self.__class__.objects.get(pk=self.pk)
        super().save(*args, **kwargs)
        event = TrackingEvent.objects.create(
            operation=TrackingEvent.CHANGE if self.pk else TrackingEvent.ADD,
            user=CuserMiddleware.get_user(),
            date=now(),
            obj=self,
        )
        for field in self._meta.fields:
            if field.name == 'id':
                continue
            value = getattr(self, field.name)
            if not change and value is not None and value != "" or change and value != getattr(old, field.name):
                TrackingValue.objects.create(
                    event=event,
                    field=field.name,
                    value=str(value)
                )

    def delete(self, *args, **kwargs):
        TrackingEvent.objects.create(
            operation=TrackingEvent.DELETE,
            user=CuserMiddleware.get_user(),
            date=now(),
            obj=self,
        )
        super().delete(*args, **kwargs)


class Agreement(TrackingMixin, models.Model):
    date = models.DateField(verbose_name="Date")
    order = models.IntegerField(verbose_name="Numéro d'ordre")
    odt = models.FileField(upload_to='conventions', blank=True)
    pdf = models.FileField(upload_to='conventions', blank=True)
    booking = models.ForeignKey('Booking', verbose_name="Réservation", related_name='agreements', null=True)

    class Meta:
        verbose_name = "Convention"
        get_latest_by = 'date'

    def number(self):
        return "{year}-{order:03}".format(year=self.date.year, order=self.order)
    number.short_description = "Numéro"

    def __str__(self):
        return self.number()


class BookingState(TrackingMixin, models.Model):
    INCOME_CHOICES = (
        (1, "Potentiel"),
        (2, "Confirmé"),
        (3, "Facturé"),
        (4, "Infirmé"),
        (5, "Annulé"),
    )
    COLOR_CHOICES = (
        ('default', "Gris"),
        ('primary', "Bleu"),
        ('success', "Vert"),
        ('info', "Cyan"),
        ('warning', "Orange"),
        ('danger', "Rouge"),
    )
    title = models.CharField(verbose_name="Intitulé", max_length=100)
    income = models.IntegerField(verbose_name="Chiffre d'affaire", choices=INCOME_CHOICES)
    color = models.CharField(verbose_name="Couleur", max_length=10, choices=COLOR_CHOICES)

    class Meta:
        verbose_name = "Statut"
        ordering = ('title', )

    def __str__(self):
        return self.title


class BookingManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.annotate(begin=Min('items__begin'), end=Max('items__end'))
        qs = qs.annotate(nights=ExtractDay(F('end') - F('begin')))
        qs = qs.annotate(headcount=Sum('items__headcount'))
        overnights = ExtractDay(F('items__end') - F('items__begin')) * F('items__headcount')
        qs = qs.annotate(overnights=ExpressionWrapper(Sum(overnights), output_field=models.DecimalField()))
        qs = qs.annotate(price=Coalesce(Sum('items__price'), 0))
        amount_pppn = ExtractDay(F('items__end') - F('items__begin')) * F('items__headcount') * F('items__price_pppn')
        qs = qs.annotate(amount_pppn=ExpressionWrapper(Coalesce(Sum(amount_pppn), 0), output_field=models.DecimalField()))
        amount_pp = F('items__headcount') * F('items__price_pp')
        qs = qs.annotate(amount_pp=ExpressionWrapper(Coalesce(Sum(amount_pp), 0), output_field=models.DecimalField()))
        amount_pn = ExtractDay(F('items__end') - F('items__begin')) * F('items__price_pn')
        qs = qs.annotate(amount_pn=ExpressionWrapper(Coalesce(Sum(amount_pn), 0), output_field=models.DecimalField()))
        sub_amount_cot = ExpressionWrapper(ExtractDay(F('items__end') - F('items__begin')) * F('items__headcount'),
                                           output_field=models.DecimalField())
        amount_cot = Case(When(items__cotisation=True, then=sub_amount_cot))
        qs = qs.annotate(amount_cot=ExpressionWrapper(Coalesce(Sum(amount_cot), 0), output_field=models.DecimalField()))
        qs = qs.annotate(amount=F('price') + F('amount_pppn') + F('amount_pp') + F('amount_pn') + F('amount_cot'))
        qs = qs.annotate(deposit=F('amount') * .3)
        qs = qs.annotate(payment=Sum('payments__amount'))
        qs = qs.annotate(balance=F('amount') - F('payment'))
        return qs


class Booking(TrackingMixin, models.Model):
    ORG_TYPE_CHOICES = (
        (1, "EEDF"),
        (2, "Scouts français"),
        (3, "Scouts étrangers"),
        (4, "Association"),
        (5, "Particulier"),
        (6, "Scolaires"),
    )
    title = models.CharField(verbose_name="Intitulé", max_length=100, blank=True)
    org_type = models.IntegerField(verbose_name="Type d'organisation", choices=ORG_TYPE_CHOICES, blank=True, null=True)
    contact = models.CharField(verbose_name="Contact", max_length=100, blank=True)
    email = models.EmailField(verbose_name="Email", blank=True)
    tel = models.CharField(verbose_name="Téléphone", max_length=12, blank=True)
    state = models.ForeignKey(BookingState, verbose_name="Statut", blank=True, null=True)
    description = models.TextField(verbose_name="Description", blank=True)
    signed_agreement = models.OneToOneField(Agreement, verbose_name="N° convention signée", blank=True, null=True,
                                            related_name='signedx_booking')
    signed_agreement_scan = models.FileField(verbose_name="Scan convention signée", upload_to='conventions_signees',
                                             blank=True)

    objects = BookingManager()

    class Meta:
        verbose_name = "Réservation"

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('booking:booking_detail', kwargs={'pk': self.pk})

    @property
    def terrain(self):
        return self.items.filter(product=1).exists()

    @property
    def village(self):
        return self.items.filter(product=2).exists()

    @property
    def agreement(self):
        return self.agreements.latest()


class BookingItemManager(models.Manager):
    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.annotate(nights=ExtractDay(F('end') - F('begin')))
        qs = qs.annotate(overnights=ExpressionWrapper(F('nights') * F('headcount'), output_field=models.DecimalField()))
        amount_pppn = Coalesce(F('overnights') * F('price_pppn'), 0)
        qs = qs.annotate(amount_pppn=ExpressionWrapper(amount_pppn, output_field=models.DecimalField()))
        amount_pp = Coalesce(F('headcount') * F('price_pp'), 0)
        qs = qs.annotate(amount_pp=ExpressionWrapper(amount_pp, output_field=models.DecimalField()))
        amount_pn = Coalesce(F('nights') * F('price_pn'), 0)
        qs = qs.annotate(amount_pn=ExpressionWrapper(amount_pn, output_field=models.DecimalField()))
        amount_cot = Coalesce(Case(When(cotisation=True, then=F('overnights'))), 0)
        qs = qs.annotate(amount_cot=ExpressionWrapper(amount_cot, output_field=models.DecimalField()))
        qs = qs.annotate(amount=Coalesce(F('price'), 0) + F('amount_pppn') + F('amount_pp') + F('amount_pn') + F('amount_cot'))
        return qs


class BookingItem(TrackingMixin, models.Model):
    PRODUCT_CHOICES = (
        (1, "Hébergement Terrain"),
        (2, "Hébergement Hameau"),
        (3, "Location matériel"),
        (4, "Refacturation"),
        (5, "Salles"),
    )
    title = models.CharField(verbose_name="Intitulé", max_length=100, blank=True)
    booking = models.ForeignKey(Booking, related_name='items', on_delete=models.CASCADE)
    headcount = models.PositiveIntegerField(verbose_name="Effectif", blank=True, null=True)
    begin = models.DateField(verbose_name="Date de début", blank=True, null=True)
    end = models.DateField(verbose_name="Date de fin", blank=True, null=True)
    product = models.IntegerField(verbose_name="Produit", choices=PRODUCT_CHOICES)
    price_pppn = models.DecimalField(verbose_name="Prix/nuitée", max_digits=8, decimal_places=2, null=True, blank=True)
    price_pn = models.DecimalField(verbose_name="Prix/nuit", max_digits=8, decimal_places=2, null=True, blank=True)
    price_pp = models.DecimalField(verbose_name="Prix/pers", max_digits=8, decimal_places=2, null=True, blank=True)
    price = models.DecimalField(verbose_name="Prix forfait", max_digits=8, decimal_places=2, null=True, blank=True)
    cotisation = models.BooleanField(verbose_name="Cotis° associé", default=True)

    objects = BookingItemManager()

    def __str__(self):
        return self.title or self.get_product_display()


class Payment(TrackingMixin, models.Model):
    MEAN_CHOICES = (
        (1, "Chèque"),
        (2, "Virement"),
        (3, "Espèces"),
    )
    mean = models.IntegerField(verbose_name="Moyen de paiement", choices=MEAN_CHOICES)
    date = models.DateField()
    amount = models.DecimalField(verbose_name="Montant", max_digits=8, decimal_places=2)
    booking = models.ForeignKey(Booking, related_name='payments', on_delete=models.CASCADE)
    scan = models.FileField(verbose_name="Scan", upload_to='paiements', blank=True)

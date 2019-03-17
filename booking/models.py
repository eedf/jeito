from datetime import timedelta
from cuser.middleware import CuserMiddleware
from django.db import models
from django.db.models import Case, ExpressionWrapper, F, Min, Max, Sum, When
from django.db.models.functions import Cast, Coalesce, ExtractDay
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.utils.timezone import now
from members.models import Structure
from members.utils import current_season, current_year


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
    event = models.ForeignKey(TrackingEvent, verbose_name="Événement", on_delete=models.PROTECT)
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
    booking = models.ForeignKey('Booking', verbose_name="Réservation", related_name='agreements',
                                on_delete=models.PROTECT)

    class Meta:
        verbose_name = "Convention"
        get_latest_by = 'date'
        ordering = ('order', )

    def number(self):
        return "{year}-{order:03}".format(year=self.booking.year, order=self.order)

    number.short_description = "Numéro"
    number.admin_order_field = 'order'

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
        ordering = ('title',)

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
        qs = qs.annotate(amount_pppn=ExpressionWrapper(Coalesce(Sum(amount_pppn), 0),
                                                       output_field=models.DecimalField()))
        amount_pp = F('items__headcount') * F('items__price_pp')
        qs = qs.annotate(amount_pp=ExpressionWrapper(Coalesce(Sum(amount_pp), 0), output_field=models.DecimalField()))
        amount_pn = ExtractDay(F('items__end') - F('items__begin')) * F('items__price_pn')
        qs = qs.annotate(amount_pn=ExpressionWrapper(Coalesce(Sum(amount_pn), 0), output_field=models.DecimalField()))
        sub_amount_cot = ExpressionWrapper(ExtractDay(F('items__end') - F('items__begin')) * F('items__headcount'),
                                           output_field=models.DecimalField())
        amount_cot = Case(When(items__cotisation=True, then=sub_amount_cot))
        qs = qs.annotate(amount_cot=ExpressionWrapper(Coalesce(Sum(amount_cot), 0), output_field=models.DecimalField()))
        qs = qs.annotate(amount=Cast(F('price') + F('amount_pppn') + F('amount_pp') + F('amount_pn') + F('amount_cot'),
                                     output_field=models.DecimalField(max_digits=8, decimal_places=2)))
        qs = qs.annotate(deposit=Cast(F('amount') * .3,
                                      output_field=models.DecimalField(max_digits=8, decimal_places=2)))
        return qs


class BookingQuerySet(models.QuerySet):
    def for_user(self, user):
        if user.is_superuser:
            return self
        return self.filter(structure__nomination__adhesion__person=user,
                           structure__nomination__adhesion__season=current_season())


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
    year = models.IntegerField(verbose_name="Année", default=current_year)
    org_type = models.IntegerField(verbose_name="Type d'organisation", choices=ORG_TYPE_CHOICES, blank=True, null=True)
    contact = models.CharField(verbose_name="Contact", max_length=100, blank=True)
    email = models.EmailField(verbose_name="Email", blank=True)
    tel = models.CharField(verbose_name="Téléphone", max_length=12, blank=True)
    state = models.ForeignKey(BookingState, verbose_name="Statut", blank=True, null=True, on_delete=models.PROTECT)
    description = models.TextField(verbose_name="Description", blank=True)
    signed_agreement = models.OneToOneField(Agreement, verbose_name="N° convention signée", blank=True, null=True,
                                            related_name='signedx_booking', on_delete=models.PROTECT)
    signed_agreement_scan = models.FileField(verbose_name="Scan convention signée", upload_to='conventions_signees',
                                             blank=True)
    insurance_scan = models.FileField(verbose_name="Attestation d'assurance", upload_to='assurance', blank=True)
    invoice = models.FileField(verbose_name="Facture", upload_to='factures', blank=True)
    invoice_number = models.CharField(max_length=10, blank=True)
    structure = models.ForeignKey(Structure, verbose_name="Structure", on_delete=models.PROTECT)
    preferred_place = models.CharField(verbose_name="Placement souhaité", max_length=1024, blank=True)
    wood = models.CharField(verbose_name="Bois", max_length=1024, blank=True)

    objects = BookingManager.from_queryset(BookingQuerySet)()

    class Meta:
        verbose_name = "Réservation"
        permissions = (('show_booking', 'Can show booking'), )
        ordering = ('-year', 'title')

    def __str__(self):
        return "{} - {}".format(self.year, self.title)

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
        agreements = list(self.agreements.all())
        if not agreements:
            return None
        agreements.sort(key=lambda agreement: agreement.date, reverse=True)
        return agreements[0]

    @property
    def payment(self):
        return sum([payment.amount for payment in self.payments.all()])

    @property
    def balance(self):
        if self.amount is None and self.payment is None:
            return None
        return (self.amount or 0) - (self.payment or 0)

    @property
    def gone(self):
        return bool(self.end) and self.end < settings.NOW().date()

    @property
    def google_id(self):
        return 'jeito{}'.format(self.id)

    @property
    def google_repr(self):
        begin = min([date for date in self.items.values_list('begin', flat=True) if date], default=None)
        end = max([date for date in self.items.values_list('end', flat=True) if date], default=None)
        if not begin or not end:
            return None
        return {
            'id': self.google_id,
            'summary': self.title + (' ?' if self.state.income == 1 else ''),
            'start': {
                'date': begin.isoformat(),
            },
            'end': {
                'date': (end + timedelta(days=1)).isoformat(),
            },
        }


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
        qs = qs.annotate(
            amount=Coalesce(F('price'), 0) + F('amount_pppn') + F('amount_pp') + F('amount_pn') + F('amount_cot'))
        return qs


class BookingItemQuerySet(models.QuerySet):
    def for_user(self, user):
        if user.is_superuser:
            return self
        return self.filter(booking__structure__nomination__adhesion__person=user,
                           booking__structure__nomination__adhesion__season=current_season())


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

    objects = BookingItemManager.from_queryset(BookingItemQuerySet)()

    def __str__(self):
        return self.title or self.get_product_display()


class Payment(TrackingMixin, models.Model):
    MEAN_CHOICES = (
        (1, "Chèque"),
        (2, "Virement"),
        (3, "Espèces"),
        (4, "ANCV"),
    )
    mean = models.IntegerField(verbose_name="Moyen de paiement", choices=MEAN_CHOICES)
    date = models.DateField()
    amount = models.DecimalField(verbose_name="Montant", max_digits=8, decimal_places=2)
    booking = models.ForeignKey(Booking, related_name='payments', on_delete=models.CASCADE)
    scan = models.FileField(verbose_name="Scan", upload_to='paiements', blank=True)

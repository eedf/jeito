from collections import defaultdict
from datetime import timedelta
from django.db import models
from tracking_fields.decorators import track


@track('type', 'name', 'firstname', 'lastname', 'tel', 'email', 'invoice', 'number', 'begin',
       'end', 'comfort', 'nights', 'overnights', 'comments', 'state')
class Group(models.Model):
    STATE_CHOICES = (
        (1, "Demande de renseignements"),
        (2, "Demande de devis"),
        (3, "Devis établi"),
        (4, "Devis signé"),
        (5, "Facture établie"),
        (6, "Facture payée"),
        (7, "Annulé"),
    )
    type = models.IntegerField(choices=((1, "EEDF"), (2, "Scout"), (3, "Extérieur")))
    name = models.CharField(max_length=100)
    firstname = models.CharField(max_length=100, blank=True)
    lastname = models.CharField(max_length=100, blank=True)
    tel = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    estimate = models.FileField(blank=True)
    invoice = models.FileField(blank=True)
    number = models.PositiveIntegerField(null=True, editable=False)
    begin = models.DateField(null=True, editable=False)
    end = models.DateField(null=True, editable=False)
    comfort = models.IntegerField(null=True, choices=((1, 'Terrain'), (2, 'Village'), (3, 'Mixte')), editable=False)
    nights = models.PositiveIntegerField(null=True, editable=False)
    overnights = models.PositiveIntegerField(null=True, editable=False)
    comments = models.TextField(blank=True)
    state = models.IntegerField(choices=STATE_CHOICES, default=1)
    hosting_cost = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, editable=False)
    coop_cost = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    additional_cost = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    cost = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, editable=False)
    invoice_number = models.CharField(max_length=10, blank=True)

    def __str__(self):
        return self.name

    def denormalize(self):
        headcounts = self.headcounts.all()
        self.begin = min([headcount.begin for headcount in headcounts] or [None])
        self.end = max([headcount.end for headcount in headcounts] or [None])
        self.nights = self.begin and self.end and (self.end - self.begin).days
        self.comfort = None
        self.hosting_cost = None
        overnights = defaultdict(int)
        for headcount in headcounts:
            self.comfort = self.comfort or headcount.comfort
            if self.comfort != headcount.comfort:
                self.comfort = 3
            nights = (headcount.end - headcount.begin).days
            if headcount.cost is not None:
                self.hosting_cost = (self.hosting_cost or 0) + (headcount.number * max(nights, 1) * headcount.cost)
            for i in range(nights):
                overnights[headcount.begin + timedelta(days=i)] += headcount.number
        self.number = max(overnights.values() or [None])
        self.overnights = sum(overnights.values() or [0]) or None
        if self.hosting_cost is None and self.coop_cost is None and self.additional_cost is None:
            self.cost = None
        else:
            self.cost = (self.hosting_cost or 0) + (self.coop_cost or 0) + (self.additional_cost or 0)

    def save(self, *args, **kwargs):
        self.denormalize()
        return super().save(*args, **kwargs)


class Headcount(models.Model):
    group = models.ForeignKey(Group, related_name='headcounts')
    number = models.PositiveIntegerField()
    begin = models.DateField()
    end = models.DateField()
    comfort = models.IntegerField(choices=((1, 'Terrain'), (2, 'Village')))
    cost = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True)
    overnights = models.PositiveIntegerField(null=True, editable=False)
    hosting_cost = models.DecimalField(max_digits=8, decimal_places=2, null=True, blank=True, editable=False)

    def __str__(self):
        return "{} p. du {} au {}".format(
            self.number,
            self.begin.strftime('%d/%m/%y'),
            self.end.strftime('%d/%m/%y'),
        )

    def denormalize(self):
        self.overnights = (self.end - self.begin).days * self.number
        self.hosting_cost = self.cost and self.cost * self.overnights

    def save(self, *args, **kwargs):
        self.denormalize()
        self.group.denormalize()
        return super().save(*args, **kwargs)

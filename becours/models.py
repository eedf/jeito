from collections import defaultdict
from datetime import timedelta
from django.db import models


class Group(models.Model):
    type = models.IntegerField(choices=((1, "EEDF"), (2, "Scout"), (3, "Extérieur")))
    name = models.CharField(max_length=100)
    firstname = models.CharField(max_length=100, blank=True)
    lastname = models.CharField(max_length=100, blank=True)
    tel = models.CharField(max_length=100, blank=True)
    email = models.EmailField(blank=True)
    invoice = models.FileField(blank=True)
    number = models.PositiveIntegerField(null=True, editable=False)
    begin = models.DateField(null=True, editable=False)
    end = models.DateField(null=True, editable=False)
    comfort = models.IntegerField(null=True, choices=((1, 'Terrain'), (2, 'Village'), (3, 'Mixte')), editable=False)
    nights = models.PositiveIntegerField(null=True, editable=False)
    overnights = models.PositiveIntegerField(null=True, editable=False)

    def __str__(self):
        return self.name

    def denormalize(self):
        headcounts = self.headcounts.all()
        self.begin = min([headcount.begin for headcount in headcounts] or [None])
        self.end = max([headcount.end for headcount in headcounts] or [None])
        self.nights = (self.end - self.begin).days
        self.comfort = None
        for headcount in headcounts:
            self.comfort = self.comfort or headcount.comfort
            if self.comfort != headcount.comfort:
                self.comfort = 3
        overnights = defaultdict(int)
        for headcount in headcounts:
            for i in range((headcount.end - headcount.begin).days):
                overnights[headcount.begin + timedelta(days=i)] += headcount.number
        self.number = max(overnights.values() or [None])
        self.overnights = sum(overnights.values() or [0]) or None

    def save(self, *args, **kwargs):
        self.denormalize()
        return super().save(*args, **kwargs)


class Headcount(models.Model):
    group = models.ForeignKey(Group, related_name='headcounts')
    number = models.PositiveIntegerField()
    begin = models.DateField()
    end = models.DateField()
    comfort = models.IntegerField(choices=((1, 'Terrain'), (2, 'Village')))

    def __str__(self):
        return "{} p. du {} au {}".format(
            self.number,
            self.begin.strftime('%d/%m/%y'),
            self.end.strftime('%d/%m/%y'),
        )

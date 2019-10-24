from django.db import models
from mptt.models import MPTTModel, TreeForeignKey


class Place(MPTTModel):
    title = models.CharField(verbose_name="Intitulé", max_length=100)
    parent = TreeForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='children')

    class Meta:
        verbose_name = "Emplacement"

    class MPTTMeta:
        order_insertion_by = ['title']

    def __str__(self):
        return self.title


class Skill(models.Model):
    title = models.CharField(verbose_name="Intitulé", max_length=100)

    class Meta:
        verbose_name = "Compétence"

    def __str__(self):
        return self.title


class Priority(models.Model):
    title = models.CharField(verbose_name="Intitulé", max_length=100)

    class Meta:
        verbose_name = "Urgence"

    def __str__(self):
        return self.title


class Issue(models.Model):
    title = models.CharField(verbose_name="Intitulé", max_length=100)
    description = models.TextField(verbose_name="Description", blank=True)
    place = models.ForeignKey(Place, verbose_name="Emplacement", null=True, blank=True, on_delete=models.PROTECT)
    skill = models.ForeignKey(Skill, verbose_name="Compétence", null=True, blank=True, on_delete=models.PROTECT)
    priority = models.ForeignKey(Priority, verbose_name="Priorité", null=True, blank=True, on_delete=models.PROTECT)
    blocks = models.ManyToManyField('self', verbose_name="Bloque", blank=True)

    class Meta:
        verbose_name = "Problème"

    def __str__(self):
        return self.title

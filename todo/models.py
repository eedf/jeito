from django.db import models


class Action(models.Model):
    title = models.CharField(max_length=100, verbose_name="Titre")
    description = models.TextField()
    deadline = models.DateField(null=True, blank=True, verbose_name="Date limite")
    done = models.BooleanField(default=False, verbose_name="Fait")
    creation = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

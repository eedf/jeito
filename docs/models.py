from tika import parser
from django.db import models
from tagulous.models import TagField, TagModel


class DocumentTags(TagModel):
    class TagMeta:
        autocomplete_view = 'docs:tags_autocomplete'


class Document(models.Model):
    file = models.FileField(u"Fichier", max_length=200, upload_to='docs/%Y/%m/%d/')
    title = models.CharField(u"Titre", max_length=200)
    tags = TagField(DocumentTags, verbose_name=u"Mots-clés", blank=True,
                    help_text="Entrez une liste de mots-clés séparés par des virgules")
    visible = models.BooleanField(u"Visible", default=True)

    def __str__(self):
        return self.title

    def text(self):
        parsed = parser.from_file(self.file.path)
        return parsed['content']

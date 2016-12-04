from django.contrib import admin
from tagulous.admin import register
from . import models


class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'tags', 'visible')
    list_filter = ('visible', )


register(models.Document, DocumentAdmin)

from django.contrib import admin
from .models import Action


@admin.register(Action)
class ActionAdmin(admin.ModelAdmin):
    list_display = ('title', 'creation', 'deadline', 'done')
    list_filter = ('done', )
    date_hierarchy = 'deadline'

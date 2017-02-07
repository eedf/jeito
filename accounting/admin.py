from django.contrib import admin
from .models import Account, Analytic, Entry


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('number', 'title')
    ordering = ('number', )


@admin.register(Analytic)
class AnalyticAdmin(admin.ModelAdmin):
    list_display = ('title', )


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ('date', 'account', 'title', 'amount', 'analytic')
    list_editable = ('analytic', )
    date_hierarchy = 'date'
    list_filter = ('account', 'analytic', )

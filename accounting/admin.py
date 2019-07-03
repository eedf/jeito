from django.contrib import admin
from django.db.models import Q
from .models import Account, Analytic, Entry, BankStatement, Transaction


class HasScanListFilter(admin.SimpleListFilter):
    title = "Justificatif"
    parameter_name = 'scan'

    def lookups(self, request, model_admin):
        return (
            ('0', "Absent"),
        )

    def queryset(self, request, queryset):
        if self.value() == '0':
            return queryset.filter(
                Q(transaction__account__number__startswith='6') |
                Q(transaction__account__number__startswith='7'),
                projected=False,
                scan=''
            )


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('number', 'title')
    search_fields = ('=number', 'title')
    ordering = ('number', )


@admin.register(Analytic)
class AnalyticAdmin(admin.ModelAdmin):
    list_display = ('title', )
    search_fields = ('title', )


class TransactionInline(admin.TabularInline):
    model = Transaction


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ('date', 'title', 'balanced', 'has_scan', 'forwarded', 'entered', 'projected')
    search_fields = ('title', 'transaction__account__title', 'transaction__analytic__title')
    date_hierarchy = 'date'
    list_filter = (HasScanListFilter, 'forwarded', 'entered', 'projected', 'transaction__analytic')
    inlines = (TransactionInline, )
    save_as = True

    def has_scan(self, obj):
        return bool(obj.scan)
    has_scan.short_description = "Justificatif"
    has_scan.boolean = True
    has_scan.admin_order_field = 'scan'


@admin.register(BankStatement)
class BankStatementAdmin(admin.ModelAdmin):
    list_display = ('date', 'number', 'scan', 'balance')
    date_hierarchy = 'date'


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    search_fields = ('title', '^account__number', 'account__title', '=expense', '=revenue')
    date_hierarchy = 'entry__date'
    list_display = ('date', 'account', 'analytic', 'title', 'expense', 'revenue', 'reconciliation')
    list_filter = ('analytic', 'account')

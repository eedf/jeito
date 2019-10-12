from django.contrib import admin
from django.db.models import Q
from .models import (Account, Analytic, Entry, BankStatement, Transaction,
                     ThirdParty, PurchaseInvoice, TransferOrder, Journal, Year)


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
                scan=''
            )


@admin.register(Year)
class YearAdmin(admin.ModelAdmin):
    list_display = ('title', 'start', 'end')
    search_fields = ('title', )


@admin.register(Journal)
class JournalAdmin(admin.ModelAdmin):
    list_display = ('number', 'title')
    search_fields = ('=number', 'title')


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('number', 'title')
    search_fields = ('=number', 'title')


@admin.register(ThirdParty)
class ThirdPartyAdmin(AccountAdmin):
    list_display = ('number', 'title', 'type', 'account', 'client_number', 'iban', 'bic')
    search_fields = ('=number', 'title', '=client_number', '=iban', '=bic')
    list_filter = ('type', )
    ordering = ('number', )


@admin.register(Analytic)
class AnalyticAdmin(admin.ModelAdmin):
    list_display = ('number', 'title')
    search_fields = ('=number', 'title')


class TransactionInline(admin.TabularInline):
    model = Transaction


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ('title', 'year', 'date', 'balanced', 'has_scan', 'exported')
    search_fields = ('title', 'transaction__account__title', 'transaction__analytic__title')
    date_hierarchy = 'date'
    list_filter = (HasScanListFilter, 'year', 'journal', 'exported', 'transaction__analytic')
    inlines = (TransactionInline, )
    save_as = True

    def has_scan(self, obj):
        return bool(obj.scan)
    has_scan.short_description = "Justificatif"
    has_scan.boolean = True
    has_scan.admin_order_field = 'scan'


@admin.register(PurchaseInvoice)
class PurchaseInvoiceAdmin(EntryAdmin):
    list_display = ('date', 'title', 'deadline', 'number', 'balanced', 'has_scan', 'exported')
    search_fields = ('title', '=number', 'transaction__account__title', 'transaction__analytic__title')
    date_hierarchy = 'deadline'
    inlines = (TransactionInline, )
    save_as = True


@admin.register(TransferOrder)
class TransferOrderAdmin(EntryAdmin):
    pass


@admin.register(BankStatement)
class BankStatementAdmin(admin.ModelAdmin):
    list_display = ('date', 'year', 'number', 'scan', 'balance')
    list_filter = ('year', )
    date_hierarchy = 'date'


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    search_fields = ('title', '^account__number', 'account__title', '=expense', '=revenue')
    date_hierarchy = 'entry__date'
    list_display = ('date', 'account', 'analytic', 'title', 'expense', 'revenue', 'reconciliation')
    list_filter = ('analytic', 'account')

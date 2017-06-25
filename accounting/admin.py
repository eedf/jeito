from django.contrib import admin
from .models import Account, Analytic, Entry, Budget, BankStatement, Transaction


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ('number', 'title')
    search_fields = ('=number', 'title')
    ordering = ('number', )


@admin.register(Analytic)
class AnalyticAdmin(admin.ModelAdmin):
    list_display = ('title', )
    search_fields = ('title', )


class TransactionAdmin(admin.TabularInline):
    model = Transaction


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    list_display = ('date', 'title', 'balanced', 'forwarded', 'entered')
    search_fields = ('title', 'transaction__account__title', 'transaction__analytic__title')
    date_hierarchy = 'date'
    list_filter = ('forwarded', 'entered', 'transaction__analytic', )
    inlines = (TransactionAdmin, )


@admin.register(Budget)
class BudgetAdmin(admin.ModelAdmin):
    list_display = ('analytic', 'amount', 'done', 'diff', 'comment')
    list_editable = ('amount', 'comment')
    search_fields = ('analytic__title', 'comment')


@admin.register(BankStatement)
class BankStatementAdmin(admin.ModelAdmin):
    list_display = ('date', 'scan', 'balance')
    date_hierarchy = 'date'

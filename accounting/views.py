from django.views.generic import ListView, DetailView
from django.db.models import Q
from django_filters.views import FilterView
from .filters import AnalyticBalanceFilter, BalanceFilter, AccountFilter, AnalyticFilter
from .models import BankStatement, Transaction


class AnalyticBalanceView(FilterView):
    template_name = "accounting/analytic_balance.html"
    filterset_class = AnalyticBalanceFilter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['revenues'] = sum([analytic.revenue or 0 for analytic in self.object_list])
        context['expenses'] = sum([analytic.expense or 0 for analytic in self.object_list])
        context['solde'] = sum([analytic.solde or 0 for analytic in self.object_list])
        context['budget_balance'] = sum([analytic.budget.amount for analytic in self.object_list
                                         if hasattr(analytic, 'budget')])
        context['diff_balance'] = sum([analytic.diff for analytic in self.object_list if analytic.diff])
        return context


class BalanceView(FilterView):
    template_name = "accounting/balance.html"
    filterset_class = BalanceFilter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['data'] = self.object_list
        context['revenues'] = sum([account.revenue for account in context['data']])
        context['expenses'] = sum([account.expense for account in context['data']])
        context['solde'] = sum([account.solde for account in context['data']])
        return context


class AccountView(FilterView):
    template_name = "accounting/account.html"
    filterset_class = AccountFilter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        solde = 0
        revenue = 0
        expense = 0
        for transaction in self.object_list:
            solde += transaction.revenue - transaction.expense
            transaction.solde = solde
            revenue += transaction.revenue
            expense += transaction.expense
        context['revenue'] = revenue
        context['expense'] = expense
        context['solde'] = solde
        return context


class AnalyticView(FilterView):
    template_name = "accounting/analytic.html"
    filterset_class = AnalyticFilter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        solde = 0
        revenue = 0
        expense = 0
        for transaction in self.object_list:
            solde += transaction.revenue - transaction.expense
            transaction.solde = solde
            revenue += transaction.revenue
            expense += transaction.expense
        context['revenue'] = revenue
        context['expense'] = expense
        context['solde'] = solde
        return context


class BankStatementView(ListView):
    model = BankStatement


class ReconciliationView(DetailView):
    template_name = 'accounting/reconciliation.html'
    model = BankStatement

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        previous = BankStatement.objects.filter(number__lt=self.object.number).latest('number')
        transactions = Transaction.objects.filter(account__number=5120000, entry__date__lte=self.object.date)
        cond = Q(reconciliation__gt=previous.date, reconciliation__lte=self.object.date) | Q(reconciliation=None)
        transactions = transactions.filter(cond)
        transactions = transactions.order_by('reconciliation', 'entry__date')
        context['transactions'] = transactions
        return context

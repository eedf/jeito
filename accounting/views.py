from django.db.models import F, Sum
from django.views.generic import ListView, TemplateView
from django_filters.views import FilterView
from .filters import AnalyticFilter
from .models import Account, BankStatement


class AnalyticBalanceView(FilterView):
    template_name = "accounting/analytic_balance.html"
    filterset_class = AnalyticFilter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['revenues'] = sum([analytic.revenue or 0 for analytic in self.object_list])
        context['expenses'] = sum([analytic.expense or 0 for analytic in self.object_list])
        context['solde'] = sum([analytic.solde or 0 for analytic in self.object_list])
        context['budget_balance'] = sum([analytic.budget.amount for analytic in self.object_list
                                         if hasattr(analytic, 'budget')])
        context['diff_balance'] = sum([analytic.diff for analytic in self.object_list if analytic.diff])
        return context


class BalanceView(TemplateView):
    template_name = "accounting/balance.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['data'] = Account.objects.annotate(
            revenue=Sum('entry__revenue'), expense=Sum('entry__expense'),
            solde=Sum(F('entry__revenue') - F('entry__expense')))
        context['revenues'] = sum([account.revenue for account in context['data']])
        context['expenses'] = sum([account.expense for account in context['data']])
        context['solde'] = sum([account.solde for account in context['data']])
        return context


class BankStatementView(ListView):
    model = BankStatement

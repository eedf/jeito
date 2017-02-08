from django.db.models import F, Sum
from django.views.generic import TemplateView, ListView
from .models import Account, Analytic, BankStatement


class AnalyticBalanceView(TemplateView):
    template_name = "accounting/analytic_balance.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['data'] = Analytic.objects.annotate(
            revenue=Sum('entry__revenue'), expense=Sum('entry__expense'),
            solde=Sum(F('entry__revenue') - F('entry__expense')),
            diff=F('budget__amount') - Sum('entry__revenue') + Sum('entry__expense'))
        context['revenues'] = sum([analytic.revenue for analytic in context['data']])
        context['expenses'] = sum([analytic.expense for analytic in context['data']])
        context['solde'] = sum([analytic.solde for analytic in context['data']])
        context['budget_balance'] = sum([analytic.budget.amount for analytic in context['data']
                                         if hasattr(analytic, 'budget')])
        context['diff_balance'] = sum([analytic.diff for analytic in context['data'] if analytic.diff])
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

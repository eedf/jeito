from django.db.models import F, Sum
from django.views.generic import TemplateView
from .models import Analytic


class BalanceView(TemplateView):
    template_name = "accounting/balance.html"

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

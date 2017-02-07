from django.db.models import F, Sum
from django.views.generic import TemplateView
from .models import Analytic


class BalanceView(TemplateView):
    template_name = "accounting/balance.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['data'] = Analytic.objects.annotate(amount=Sum('entry__amount'),
                                                    diff=F('budget__amount') - Sum('entry__amount'))
        context['balance'] = sum([analytic.amount for analytic in context['data']])
        context['budget_balance'] = sum([analytic.budget.amount for analytic in context['data']])
        context['diff_balance'] = sum([analytic.diff for analytic in context['data']])
        return context

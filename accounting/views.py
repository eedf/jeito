from django.db.models import Sum
from django.views.generic import TemplateView
from .models import Entry


class BalanceView(TemplateView):
    template_name = "accounting/balance.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['data'] = Entry.objects.values('analytic__title').annotate(amount=Sum('amount'))
        context['balance'] = sum([entry['amount'] for entry in context['data']])
        return context

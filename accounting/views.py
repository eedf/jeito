from csv import DictWriter, QUOTE_NONNUMERIC
from collections import OrderedDict
from datetime import date, timedelta
from django.conf import settings
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import F, Q, Sum, Case, When, Value
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.utils.formats import date_format
from django.views.generic import ListView, DetailView, TemplateView, View
from django_filters.views import FilterView
from .filters import BalanceFilter, AccountFilter, EntryFilter, BudgetFilter, BankStatementFilter
from .models import BankStatement, Transaction, Entry, TransferOrder, ThirdParty, Letter


class UserMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_becours


class BudgetView(UserMixin, FilterView):
    template_name = "accounting/budget.html"
    filterset_class = BudgetFilter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self.object_list
        qs = qs.filter(account__number__regex=r'^[67]')
        qs = qs.values('analytic__id', 'analytic__title')
        qs = qs.annotate(solde_real=Sum(Case(When(entry__projected=False, then=F('revenue') - F('expense')),
                                             default=Value(0))),
                         solde_proj=Sum(Case(When(entry__projected=True, then=F('revenue') - F('expense')),
                                             default=Value(0))))
        qs = qs.order_by('analytic__title')
        for row in qs:
            row['solde_total'] = row['solde_real'] + row['solde_proj']
        context['data'] = qs
        context['solde_real'] = sum([account['solde_real'] for account in qs])
        context['solde_proj'] = sum([account['solde_proj'] for account in qs])
        context['solde_total'] = sum([account['solde_total'] for account in qs])
        return context


class ProjectionView(UserMixin, FilterView):
    template_name = "accounting/projection.html"
    filterset_class = BudgetFilter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        qs = self.object_list
        qs = qs.filter(account__number__regex=r'^[67]')
        qs = qs.values('account_id', 'account__number', 'account__title', 'analytic__id', 'analytic__title')
        qs = qs.order_by('account__number', 'analytic__title')
        qs = qs.annotate(solde=Sum(F('revenue') - F('expense')))
        context['data'] = qs
        context['solde'] = sum([account['solde'] for account in qs])
        return context


class AnalyticBalanceView(UserMixin, FilterView):
    template_name = "accounting/analytic_balance.html"
    filterset_class = BalanceFilter

    def get_filterset_kwargs(self, filterset_class):
        kwargs = super().get_filterset_kwargs(filterset_class)
        kwargs['aggregate'] = 'analytic'
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['data'] = self.object_list
        context['revenues'] = sum([analytic['revenues'] for analytic in self.object_list])
        context['expenses'] = sum([analytic['expenses'] for analytic in self.object_list])
        context['balance'] = sum([analytic['balance'] for analytic in self.object_list])
        return context


class ThirdPartyBalanceView(UserMixin, FilterView):
    template_name = "accounting/thirdparty_balance.html"
    filterset_class = BalanceFilter

    def get_filterset_kwargs(self, filterset_class):
        kwargs = super().get_filterset_kwargs(filterset_class)
        kwargs['aggregate'] = 'thirdparty'
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['data'] = self.object_list
        context['revenues'] = sum([thirdparty['revenues'] for thirdparty in self.object_list])
        context['expenses'] = sum([thirdparty['expenses'] for thirdparty in self.object_list])
        context['balance'] = sum([thirdparty['balance'] for thirdparty in self.object_list])
        return context


class BalanceView(UserMixin, FilterView):
    template_name = "accounting/balance.html"
    filterset_class = BalanceFilter

    def get_filterset_kwargs(self, filterset_class):
        kwargs = super().get_filterset_kwargs(filterset_class)
        kwargs['aggregate'] = 'account'
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['data'] = self.object_list
        context['revenues'] = sum([account['revenues'] for account in self.object_list])
        context['expenses'] = sum([account['expenses'] for account in self.object_list])
        context['balance'] = sum([account['balance'] for account in self.object_list])
        return context


class AccountView(UserMixin, FilterView):
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

    def post(self, request):
        ids = [
            key[6:] for key, val in self.request.POST.items()
            if key.startswith('letter') and val == 'on'
        ]
        transactions = Transaction.objects.filter(id__in=ids)
        if transactions.filter(letter__isnull=False).exists():
            return HttpResponse("Certaines transactions sont déjà lettrées")
        if sum([transaction.balance for transaction in transactions]) != 0:
            return HttpResponse("Le lettrage n'est pas équilibré")
        if len(set([transaction.account_id for transaction in transactions])) > 1:
            return HttpResponse("Le lettrage doit concerner un seul compte général")
        if len(set([transaction.thirdparty_id for transaction in transactions])) > 1:
            return HttpResponse("Le lettrage doit concerner un seul tiers")
        if transactions:
            transactions.update(letter=Letter.objects.create())
        return HttpResponseRedirect(request.get_full_path())


class EntryListView(UserMixin, FilterView):
    template_name = "accounting/entry_list.html"
    filterset_class = EntryFilter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        revenue = 0
        expense = 0
        balance = 0
        for entry in self.object_list:
            revenue += entry.revenue
            expense += entry.expense
            balance += entry.balance
        context['revenue'] = revenue
        context['expense'] = expense
        context['balance'] = balance
        return context


class BankStatementView(UserMixin, FilterView):
    model = BankStatement
    template_name = "accounting/bankstatement_list.html"
    filterset_class = BankStatementFilter


class ReconciliationView(UserMixin, DetailView):
    template_name = 'accounting/reconciliation.html'
    model = BankStatement

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            previous = BankStatement.objects.filter(date__lt=self.object.date).latest('date')
        except BankStatement.DoesNotExist:
            cond = Q()
        else:
            cond = Q(reconciliation__gt=previous.date)
        transactions = Transaction.objects.filter(account__number=5120000)
        transactions = transactions.filter(entry__projected=False)
        cond = cond & Q(reconciliation__lte=self.object.date) | \
            Q(reconciliation=None, entry__date__lte=self.object.date)
        transactions = transactions.filter(cond)
        transactions = transactions.order_by('reconciliation', 'entry__date')
        context['transactions'] = transactions
        return context


class NextReconciliationView(UserMixin, ListView):
    template_name = 'accounting/next_reconciliation.html'

    def get_queryset(self):
        try:
            last = BankStatement.objects.latest('date')
        except BankStatement.DoesNotExist:
            cond = Q()
        else:
            cond = Q(reconciliation__gt=last.date)
        qs = Transaction.objects.filter(account__number=5120000)
        qs = qs.filter(entry__projected=False)
        cond = cond & Q(reconciliation__lte=date.today()) | Q(reconciliation=None)
        qs = qs.filter(cond)
        qs = qs.order_by('reconciliation', 'entry__date')
        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        transactions = Transaction.objects.filter(account__number='5120000', reconciliation__lte=date.today())
        sums = transactions.aggregate(expense=Sum('expense'), revenue=Sum('revenue'))
        context['balance'] = sums['expense'] - sums['revenue']
        return context


class EntryView(UserMixin, DetailView):
    model = Entry

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['transactions'] = self.object.transaction_set.order_by('account__number', 'analytic__title')
        return context


class CashFlowView(UserMixin, TemplateView):
    template_name = 'accounting/cash_flow.html'


class CashFlowJsonView(UserMixin, View):
    def serie(self, season, GET):
        self.today = (settings.NOW() - timedelta(days=1)).date()
        start = date(season, 1, 1)
        end = min(date(season, 12, 31), self.today)
        qs = Transaction.objects.filter(account__number__in=('5120000', '5300000'), reconciliation__year=season)
        qs = qs.order_by('-reconciliation').values('reconciliation').annotate(balance=Sum('revenue') - Sum('expense'))
        qs = list(qs)
        data = OrderedDict()
        dates = [start + timedelta(days=n) for n in
                 range((end - start).days + 1)]
        balance = 0
        for d in dates:
            if qs and qs[-1]['reconciliation'] == d:
                balance += qs.pop()['balance']
            if d.month == 2 and d.day == 29:
                continue
            data[d] = -balance
        return data

    def get(self, request):
        season = settings.NOW().year
        reference = season - 1
        data = self.serie(season, self.request.GET)
        ref_data = self.serie(reference, self.request.GET)
        date_max = max(data.keys())
        ref_date_max = date_max.replace(year=reference)
        date1 = ref_date_max.strftime('%d/%m/%Y')
        date2 = date_max.strftime('%d/%m/%Y')
        nb1 = ref_data[ref_date_max]
        nb2 = data[date_max]
        diff = nb2 - nb1
        if nb1:
            percent = 100 * diff / nb1
            comment = """Au <strong>{}</strong> : <strong>{:+0.2f}</strong> €<br>
                         Au <strong>{}</strong> : <strong>{:+0.2f}</strong> €,
                         c'est-à-dire <strong>{:+0.2f}</strong> €
                         (<strong>{:+0.1f} %</strong>)
                      """.format(date1, nb1, date2, nb2, diff, percent)
        else:
            comment = """Au <strong>{}</strong> : <strong>{:+0.2f}</strong> €
                      """.format(date2, nb2)
        data = {
            'labels': [date_format(x, 'b') if x.day == 1 else '' for x in ref_data.keys()],
            'series': [
                list(ref_data.values()),
                list(data.values()),
            ],
            'comment': comment,
        }
        return JsonResponse(data)


class TransferOrderDownloadView(DetailView):
    model = TransferOrder

    def render_to_response(self, context, **response_kwargs):
        return HttpResponse(self.object.sepa(), content_type='application/xml')


class ThirdPartyCsvView(ListView):
    model = ThirdParty
    fields = ('number', 'title', 'type', 'account_number', 'iban', 'bic')

    def render_to_response(self, context):
        response = HttpResponse(content_type='text/csv; charset=cp1252')
        writer = DictWriter(response, self.fields, delimiter=';', quoting=QUOTE_NONNUMERIC)
        writer.writeheader()
        for obj in self.object_list:
            writer.writerow({field: getattr(obj, field) for field in self.fields})
        return response


class EntryCsvView(ListView):
    queryset = Transaction.objects \
        .filter(entry__date__year=2019, entry__projected=False, entry__entered=False) \
        .order_by('entry__id', 'id') \
        .select_related('entry', 'entry__journal', 'account', 'thirdparty')
    fields = (
        'journal_number', 'date_dmy', 'account_number', 'entry_id',
        'thirdparty_number', '__str__', 'expense', 'revenue'
    )

    def render_to_response(self, context):
        response = HttpResponse(content_type='text/csv; charset=cp1252')
        writer = DictWriter(response, self.fields, delimiter=';', quoting=QUOTE_NONNUMERIC)
        writer.writeheader()

        def get_value(obj, field):
            value = getattr(obj, field)
            if callable(value):
                value = value()
            return value

        for obj in self.object_list:
            writer.writerow({field: get_value(obj, field) for field in self.fields})
        return response

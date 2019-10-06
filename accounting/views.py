from csv import DictWriter, QUOTE_NONNUMERIC
from collections import OrderedDict
from datetime import date, timedelta
from django.conf import settings
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.exceptions import ImproperlyConfigured
from django.db.models import F, Q, Sum
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.urls import reverse_lazy
from django.utils.formats import date_format
from django.views.generic import ListView, DetailView, TemplateView, View
from django.views.generic.base import ContextMixin, TemplateResponseMixin
from django_filters.views import FilterView
from .filters import BalanceFilter, AccountFilter, EntryFilter, ProjectionFilter, BankStatementFilter
from .forms import PurchaseForm, PurchaseFormSet
from .models import (BankStatement, Transaction, Entry, TransferOrder, ThirdParty,
                     Letter, PurchaseInvoice, Journal, Account)


class UserMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and self.request.user.is_becours


class ProjectionView(UserMixin, FilterView):
    template_name = "accounting/projection.html"
    filterset_class = ProjectionFilter

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
        .filter(entry__date__year=2019, entry__entered=False) \
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


class ChecksView(TemplateView):
    template_name = 'accounting/checks.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        transactions = Transaction.objects.filter(entry__date__year=2019)
        context['missing_analytic'] = transactions.filter(account__number__regex=r'^[67]', analytic__isnull=True)
        context['extraneous_analytic'] = transactions.filter(account__number__regex=r'^[^67]', analytic__isnull=False)
        return context


class FormsMixin(ContextMixin):
    """Provide a way to show and handle multiple forms in a request."""
    initials = None
    form_classes = None
    success_url = None
    prefixes = None

    def get_initials(self):
        """Return the initial data to use for forms on this view."""
        if self.initials is None:
            return [{} for form in self.get_form_classes()]
        return [initial.copy() for initial in self.initials]

    def get_prefixes(self):
        """Return the prefixes to use for forms."""
        if self.prefixes is None:
            return [None for form in self.get_form_classes()]
        return self.prefixes

    def get_form_classes(self):
        """Return the form classes to use."""
        return self.form_classes

    def get_forms(self, form_classes=None):
        """Return an instance of each form to be used in this view."""
        if form_classes is None:
            form_classes = self.get_form_classes()
        return [cls(**kwargs) for cls, kwargs in zip(form_classes, self.get_forms_kwargs())]

    def get_forms_kwargs(self):
        """Return the keyword arguments for instantiating the forms."""
        kwargs_list = []
        for initial, prefix in zip(self.get_initials(), self.get_prefixes()):
            kwargs = {
                'initial': initial,
                'prefix': prefix,
            }

            if self.request.method in ('POST', 'PUT'):
                kwargs.update({
                    'data': self.request.POST,
                    'files': self.request.FILES,
                })
            kwargs_list.append(kwargs)
        return kwargs_list

    def get_success_url(self):
        """Return the URL to redirect to after processing a valid form."""
        if not self.success_url:
            raise ImproperlyConfigured("No URL to redirect to. Provide a success_url.")
        return str(self.success_url)  # success_url may be lazy

    def forms_valid(self, forms):
        """If the forms are valid, redirect to the supplied URL."""
        return HttpResponseRedirect(self.get_success_url())

    def forms_invalid(self, forms):
        """If the forms are invalid, render the invalid forms."""
        return self.render_to_response(self.get_context_data(forms=forms))

    def get_context_data(self, **kwargs):
        """Insert the forms into the context dict."""
        if 'forms' not in kwargs:
            kwargs['forms'] = self.get_forms()
        return super().get_context_data(**kwargs)


class ProcessFormsView(View):
    """Render forms on GET and processes it on POST."""
    def get(self, request, *args, **kwargs):
        """Handle GET requests: instantiate a blank version of the forms."""
        return self.render_to_response(self.get_context_data())

    def post(self, request, *args, **kwargs):
        """
        Handle POST requests: instantiate form instances with the passed
        POST variables and then check if it's valid.
        """
        forms = self.get_forms()
        if all([form.is_valid() for form in forms]):
            return self.forms_valid(forms)
        else:
            return self.forms_invalid(forms)

    # PUT is a valid HTTP verb for creating (with a known URL) or editing an
    # object, note that browsers only support POST for now.
    def put(self, *args, **kwargs):
        return self.post(*args, **kwargs)


class BaseFormsView(FormsMixin, ProcessFormsView):
    """A base view for displaying forms."""


class FormsView(TemplateResponseMixin, BaseFormsView):
    """A view for displaying forms and rendering a template response."""


class PurchaseCreateView(UserMixin, FormsView):
    template_name = 'accounting/purchase_form.html'
    form_classes = [PurchaseForm, PurchaseFormSet]
    success_url = reverse_lazy('accounting:entry_list')

    def forms_valid(self, forms):
        purchase = PurchaseInvoice.objects.create(
            date=forms[0].cleaned_data['date'],
            title=forms[0].cleaned_data['title'],
            journal=Journal.objects.get(number="HA"),
            scan=forms[0].cleaned_data['document'],
            deadline=forms[0].cleaned_data['deadline'],
            number=forms[0].cleaned_data['number'],
        )
        for form in forms[1]:
            if not form.cleaned_data:
                continue
            Transaction.objects.create(
                entry=purchase,
                account=form.cleaned_data['account'],
                analytic=form.cleaned_data['analytic'],
                expense=form.cleaned_data['amount'],
            )
        Transaction.objects.create(
            entry=purchase,
            account=Account.objects.get(number='4010000'),
            thirdparty=forms[0].cleaned_data['provider'],
            revenue=forms[0].cleaned_data['amount'],
        )
        return super().forms_valid(forms)

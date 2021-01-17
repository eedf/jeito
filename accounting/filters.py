from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from django import forms
from django.db.models import Sum, Q
import django_filters
from .models import Analytic, Account, ThirdParty, Transaction


class BaseFilterForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.attrs = {'id': 'filter'}
        self.helper.form_class = 'form-inline'
        self.helper.field_template = 'bootstrap3/layout/inline_field_with_label.html'
        self.helper.form_method = 'get'


class BalanceFilterForm(BaseFilterForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.layout = Layout(
            'balance',
        )


class BalanceFilter(django_filters.FilterSet):
    balance = django_filters.ChoiceFilter(label="Solde", choices=(('D', "Débiteur"), ('C', "Créditeur")),
                                          method='filter_balance')

    class Meta:
        model = Transaction
        fields = ('balance', )
        form = BalanceFilterForm

    def __init__(self, aggregate, data, *args, **kwargs):
        self.aggregate = aggregate
        super().__init__(data, *args, **kwargs)
        self.queryset = self.queryset.exclude(**{self.aggregate: None})
        self.queryset = self.queryset.values(
            *(self.aggregate + '__id', self.aggregate + '__number', self.aggregate + '__title')
        )
        self.queryset = self.queryset.annotate(
            revenues=Sum('revenue'), expenses=Sum('expense'), balance=Sum('revenue') - Sum('expense')
        )
        self.queryset = self.queryset.order_by(*(self.aggregate + '__number', ))

    def filter_balance(self, qs, name, value):
        if value == 'D':
            return qs.filter(balance__lt=0)
        if value == 'C':
            return qs.filter(balance__gt=0)
        return qs


class ThirdPartyFilterForm(BaseFilterForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.layout = Layout(
            'type',
            'balance',
        )


class ThirdPartyFilter(django_filters.FilterSet):
    BALANCE_CHOICES = (
        ('C', "Créditeur"),
        ('CX', "Créditeur (hors avances)"),
        ('D', "Débiteur"),
        ('DX', "Débiteur (hors avances)"),
        ('N', "Non nul"),
        ('NX', "Non nul (hors avances)"),
        ('Z', "Nul"),
        ('ZX', "Nul (hors avances)"),
    )
    balance = django_filters.ChoiceFilter(label="Solde", choices=BALANCE_CHOICES, method='filter_balance')

    class Meta:
        model = ThirdParty
        fields = ('type', 'balance', )
        form = ThirdPartyFilterForm

    def filter_balance(self, qs, name, value):
        if value == 'C':
            return qs.filter(balance__gt=0)
        if value == 'CX':
            return qs.filter(balancex__gt=0)
        if value == 'D':
            return qs.filter(balance__lt=0)
        if value == 'DX':
            return qs.filter(balancex__lt=0)
        if value == 'N':
            return qs.exclude(balance=0)
        if value == 'NX':
            return qs.exclude(balancex=0)
        if value == 'Z':
            return qs.filter(balance=0)
        if value == 'ZX':
            return qs.filter(balancex=0)
        return qs


class AccountFilterForm(BaseFilterForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.layout = Layout(
            'account',
            'thirdparty',
            'analytic',
            'lettered',
        )


class AccountFilter(django_filters.FilterSet):
    account = django_filters.ModelChoiceFilter(label="Compte", queryset=Account.objects)
    thirdparty = django_filters.ModelChoiceFilter(label="Tiers", queryset=ThirdParty.objects)
    analytic = django_filters.ModelChoiceFilter(label="Compte analytique", queryset=Analytic.objects)
    lettered = django_filters.BooleanFilter(label="Lettré", method='filter_lettered')

    class Meta:
        model = Transaction
        fields = ('account', 'thirdparty', 'analytic', 'lettered')
        form = AccountFilterForm

    @property
    def qs(self):
        qs = super().qs.order_by('entry__date')
        qs = qs.select_related('entry', 'account', 'thirdparty', 'analytic')
        return qs

    def filter_lettered(self, qs, name, value):
        qs = qs.filter(Q(account__number__startswith='4') | Q(account__number__startswith='511'))
        qs = qs.exclude(letter__isnull=value)
        return qs

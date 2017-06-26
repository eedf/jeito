from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from django import forms
from django.conf import settings
from django.db.models import F, Sum
from django.http import QueryDict
import django_filters
from .models import Analytic, Account


class YearFilterForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-inline'
        self.helper.field_template = 'bootstrap3/layout/inline_field_with_label.html'
        self.helper.form_method = 'get'
        self.helper.layout = Layout(
            'year',
        )


class AnalyticFilter(django_filters.FilterSet):
    year = django_filters.ChoiceFilter(label="Exercice", choices=[(i, i) for i in range(settings.NOW().year, 2015, -1)],
                                       name='transaction__entry__date', lookup_expr='year')

    class Meta:
        model = Analytic
        fields = ('year', )
        form = YearFilterForm

    @property
    def qs(self):
        qs = super().qs.order_by('title')
#        qs = qs.prefetch_related('entry_set')
        qs = qs.annotate(revenue=Sum('transaction__revenue'),
                         expense=Sum('transaction__expense'),
                         solde=Sum(F('transaction__revenue') - F('transaction__expense')),
                         diff=F('budget__amount') - Sum(F('transaction__revenue') - F('transaction__expense')))
        return qs

    def __init__(self, data, *args, **kwargs):
        if data is None:
            data = QueryDict('year={}'.format(settings.NOW().year))
        super().__init__(data, *args, **kwargs)


class AccountFilter(django_filters.FilterSet):
    year = django_filters.ChoiceFilter(label="Exercice", choices=[(i, i) for i in range(settings.NOW().year, 2015, -1)],
                                       name='transaction__entry__date', lookup_expr='year')

    class Meta:
        model = Account
        fields = ('year', )
        form = YearFilterForm

    @property
    def qs(self):
        qs = super().qs.annotate(revenue=Sum('transaction__revenue'), expense=Sum('transaction__expense'),
                                 solde=Sum(F('transaction__revenue') - F('transaction__expense')))
        return qs

    def __init__(self, data, *args, **kwargs):
        if data is None:
            data = QueryDict('year={}'.format(settings.NOW().year))
        super().__init__(data, *args, **kwargs)

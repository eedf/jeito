from crispy_forms.helper import FormHelper
from crispy_forms.layout import HTML, Layout
from django import forms
from django.db.models import F, Sum
import django_filters
from .models import Analytic


# TODO: add a reinit button
class AnalyticFilterForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-inline'
        self.helper.field_template = 'bootstrap3/layout/inline_field_with_label.html'
        self.helper.form_method = 'get'
        self.helper.layout = Layout(
            'date',
            HTML("""<button type="submit" class=\"btn btn-success\">
                    <span class="glyphicon glyphicon-ok-sign"></span> Appliquer
                    </button>"""),
       )


class AnalyticFilter(django_filters.FilterSet):
    date = django_filters.DateFromToRangeFilter(label="Période", name='entry__date')

    class Meta:
        model = Analytic
        fields = ('date', )
        form = AnalyticFilterForm

    @property
    def qs(self):
        qs = super().qs.order_by('title')
#        qs = qs.prefetch_related('entry_set')
        qs = qs.annotate(revenue=Sum('entry__revenue'),
                         expense=Sum('entry__expense'),
                         solde=Sum(F('entry__revenue') - F('entry__expense')),
                         diff=F('budget__amount') - Sum(F('entry__revenue') - F('entry__expense')))
        return qs

from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
import datetime
from django import forms
from django.conf import settings
import django_filters
from .utils import first_season, current_season
from .models import Adhesion, Function, Rate


# TODO: add a reinit button
class AdhesionFilterForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['season'].initial = current_season()
        self.helper = FormHelper()
        self.helper.form_class = 'form-inline'
        self.helper.field_template = 'bootstrap3/layout/inline_field_with_label.html'
        self.helper.form_method = 'get'
        self.helper.layout = Layout(
            'season',
            'sector',
            'units',
            'function',
            'rate',
            'date2date',
        )


class AdhesionFilter(django_filters.FilterSet):
    season_choices = [(i, "{}/{}".format(i - 1, i)) for i in range(current_season(), first_season() - 1, -1)]
    sector_choices = (
        (1, 'SLA & régions'),
        (2, 'Services vacances'),
        (3, 'Centres permanents'),
    )
    units_choices = (
        (7, "Lutins"),
        (1, "Louveteaux"),
        (13, "Eclés"),
        (2, "Ainés"),
        (99, "Autres"),
    )
    function_choices = ((None, "Toutes"),) + Function.CATEGORY_CHOICES
    rate_choices = ((None, "Tous"),) + Rate.CATEGORY_CHOICES
    SVN_NUMBERS = ('0300000200', '0500000100', '1900140100')
    CPN_NUMBERS = tuple(a + b for a, b in zip(('18000002', '14005719', '27000006', '17000003', '27000005'),
                                              ('00', '01', '02', '03', '04')))

    season = django_filters.ChoiceFilter(label="Saison", choices=season_choices, empty_label=None)
    sector = django_filters.ChoiceFilter(label="Secteur", choices=sector_choices, empty_label="Tous",
                                         method='filter_sector')
    units = django_filters.ChoiceFilter(label="Unités", choices=units_choices, empty_label="Toutes",
                                        method='filter_units')
    function = django_filters.ChoiceFilter(name='nomination__function__category', label="Fonction",
                                           choices=Function.CATEGORY_CHOICES, empty_label="Toutes")
    rate = django_filters.ChoiceFilter(name='rate__category', label="Tarif",
                                       choices=Rate.CATEGORY_CHOICES, empty_label="Tous")
    date2date = django_filters.BooleanFilter(label="Date à date", widget=forms.CheckboxInput,
                                             method='filter_date')

    class Meta:
        model = Adhesion
        fields = ('season', 'sector', 'units', 'function', 'rate', 'date2date')
        form = AdhesionFilterForm

    def __init__(self, data, *args, **kwargs):
        data = data.copy()
        data.setdefault('season', current_season())
        if kwargs.pop('ref', False):
            data['season'] = int(data['season']) - 1
        super(AdhesionFilter, self).__init__(data, *args, **kwargs)

    @property
    def qs(self):
        # deduplicate multiple functions
        return super().qs.filter(nomination__main=True)

    def filter_sector(self, qs, name, value):
        if value == '1':
            qs = qs.exclude(structure__number__in=self.SVN_NUMBERS + self.CPN_NUMBERS)
        elif value == '2':
            qs = qs.filter(structure__number__in=self.SVN_NUMBERS)
        elif value == '3':
            qs = qs.filter(structure__number__in=self.CPN_NUMBERS)
        return qs

    def filter_units(self, qs, name, value):
        if value == '99':
            qs = qs.exclude(structure__type__in=(1, 2, 7, 13))
        elif value:
            qs = qs.filter(structure__type=value)
        return qs

    def filter_date(self, qs, name, value):
        season = int(self.form.cleaned_data['season'])
        if value or season == current_season():
            self.date = (settings.NOW() - datetime.timedelta(days=1)).date()
            self.date = self.date.replace(year=season if self.date.month <= 8 else season - 1)
            qs = qs.filter(date__lte=self.date)
        else:
            self.date = datetime.date(season, 8, 31)
        return qs

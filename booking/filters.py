import datetime
from django.conf import settings
from django.forms import CheckboxSelectMultiple
from django.http import QueryDict
import django_filters
from members.models import Structure
from members.utils import current_season
from .forms import BookingFilterForm, CotisationsForm
from .models import Booking, BookingState, BookingItem


def structures_queryset(request):
    return Structure.objects.centers().for_user(request.user).order_by('name')


class BookingFilter(django_filters.FilterSet):
    initial_query = 'state=3&state=4&state=5&state=6&state=7&state=9&state=11'

    structure = django_filters.ModelChoiceFilter(label="Centre", queryset=structures_queryset, field_name='structure')
    year_choices = [(year, str(year)) for year in range(settings.NOW().year, 2015, -1)]
    year = django_filters.ChoiceFilter(label="Année", choices=year_choices, field_name='begin__year')
    month = django_filters.ChoiceFilter(label="Mois", choices=[('%2d' % m, m) for m in range(1, 13)],
                                        field_name='begin__month')
    org_type = django_filters.ChoiceFilter(label="Type d'org°", choices=Booking.ORG_TYPE_CHOICES)
    state = django_filters.ModelMultipleChoiceFilter(label="Statut", queryset=BookingState.objects.all(),
                                                     widget=CheckboxSelectMultiple)

    class Meta:
        model = Booking
        fields = ('structure', 'year', 'month', 'org_type', 'state')
        form = BookingFilterForm

    def __init__(self, data, *args, **kwargs):
        if data is None:
            data = QueryDict(self.initial_query)
        super().__init__(data, *args, **kwargs)

    @property
    def qs(self):
        qs = super().qs.order_by('begin')
        qs = qs.select_related('state')
        qs = qs.prefetch_related('agreements', 'payments')
        return qs


class StatsFilter(BookingFilter):
    initial_query = "state=11&state=9&state=8&state=6&year={}".format(settings.NOW().year)


class BookingItemFilter(django_filters.FilterSet):
    structure = django_filters.ModelChoiceFilter(label="Centre", queryset=structures_queryset,
                                                 field_name='booking__structure')
    year_choices = [(year, str(year)) for year in range(settings.NOW().year, 2015, -1)]
    year = django_filters.ChoiceFilter(label="Année", choices=year_choices, field_name='begin__year')
    month = django_filters.ChoiceFilter(label="Mois", choices=[('%2d' % m, m) for m in range(1, 13)],
                                        field_name='begin__month')
    org_type = django_filters.ChoiceFilter(label="Type d'org°", choices=Booking.ORG_TYPE_CHOICES,
                                           field_name="booking__org_type")
    state = django_filters.ModelMultipleChoiceFilter(label="Statut", queryset=BookingState.objects.all(),
                                                     widget=CheckboxSelectMultiple, field_name='booking__state')

    class Meta:
        model = BookingItem
        fields = ('structure', 'year', 'month', 'org_type', 'state')
        form = BookingFilterForm

    def __init__(self, data, *args, **kwargs):
        if data is None:
            data = QueryDict('state=3&state=4&state=5&state=6&state=7&state=9&state=11')
        super().__init__(data, *args, **kwargs)

    @property
    def qs(self):
        qs = super().qs.select_related('booking', 'booking__state')
        return qs


class CotisationsFilter(django_filters.FilterSet):
    structure = django_filters.ModelChoiceFilter(label="Centre", queryset=structures_queryset,
                                                 field_name='booking__structure')
    year_choices = [(year, "{}/{}".format(year - 1, year)) for year in range(current_season(), 2016, -1)]
    year = django_filters.ChoiceFilter(label="Année", choices=year_choices, method='filter_year')
    org_type = django_filters.ChoiceFilter(label="Type d'org°", choices=Booking.ORG_TYPE_CHOICES,
                                           field_name="booking__org_type")
    state = django_filters.ModelMultipleChoiceFilter(label="Statut", queryset=BookingState.objects.all(),
                                                     widget=CheckboxSelectMultiple, field_name='booking__state')

    class Meta:
        model = BookingItem
        fields = ('structure', 'year', 'org_type', 'state')
        form = CotisationsForm

    def __init__(self, data, *args, **kwargs):
        if data is None:
            data = QueryDict('state=8&state=9&state=11&year={}'.format(current_season()))
        super().__init__(data, *args, **kwargs)

    def filter_year(self, qs, name, value):
        year = int(value)
        return qs.filter(end__gt=datetime.date(year - 1, 9, 1), begin__lte=datetime.date(year, 8, 31))

    @property
    def qs(self):
        qs = super().qs.filter(cotisation=True, headcount__isnull=False)
        qs = qs.select_related('booking', 'booking__state')
        qs = qs.order_by('begin', 'end')
        return qs

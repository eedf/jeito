from django.conf import settings
from django.forms import CheckboxSelectMultiple
from django.http import QueryDict
import django_filters
from members.models import Structure
from .forms import BookingFilterForm, BookingItemFilterForm
from .models import Booking, BookingState, BookingItem


def structures_queryset(request):
    return Structure.objects.centers().for_user(request.user).order_by('name')


class BookingFilter(django_filters.FilterSet):
    structure = django_filters.ModelChoiceFilter(label="Centre", queryset=structures_queryset, name='structure')
    year_choices = [(year, str(year)) for year in range(settings.NOW().year, 2015, -1)]
    year = django_filters.ChoiceFilter(label="Année", choices=year_choices, name='begin__year')
    org_type = django_filters.ChoiceFilter(label="Type d'org°", choices=Booking.ORG_TYPE_CHOICES)
    state = django_filters.ModelMultipleChoiceFilter(label="Statut", queryset=BookingState.objects.all(),
                                                     widget=CheckboxSelectMultiple)

    class Meta:
        model = Booking
        fields = ('structure', 'year', 'org_type', 'state')
        form = BookingFilterForm

    def __init__(self, data, *args, **kwargs):
        if data is None:
            data = QueryDict('state=3&state=4&state=5&state=6&state=7&state=9&state=11')
        super().__init__(data, *args, **kwargs)

    @property
    def qs(self):
        qs = super().qs.order_by('begin')
        qs = qs.select_related('state')
        qs = qs.prefetch_related('agreements', 'payments')
        return qs


class BookingItemFilter(django_filters.FilterSet):
    structure = django_filters.ModelChoiceFilter(label="Centre", queryset=structures_queryset,
                                                 name='booking__structure')
    state = django_filters.ModelMultipleChoiceFilter(label="Statut", queryset=BookingState.objects.all(),
                                                     widget=CheckboxSelectMultiple, name='booking__state')

    class Meta:
        model = BookingItem
        fields = ('structure', 'state')
        form = BookingItemFilterForm

    def __init__(self, data, *args, **kwargs):
        if data is None:
            data = QueryDict('state=3&state=4&state=5&state=6&state=7&state=9&state=11')
        super().__init__(data, *args, **kwargs)

    @property
    def qs(self):
        qs = super().qs.filter(end__gt=settings.NOW().date()).select_related('booking', 'booking__state')
        return qs

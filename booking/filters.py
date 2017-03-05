from crispy_forms.bootstrap import InlineCheckboxes
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout
from django import forms
from django.conf import settings
from django.db.models import Q
from django.http import QueryDict
import django_filters
from members.models import Structure
from .models import Booking, BookingState, BookingItem


# TODO: add a reinit button
# TODO: use https://behigh.github.io/bootstrap_dropdowns_enhancement
class BookingFilterForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['year'].initial = settings.NOW().year
        self.helper = FormHelper()
        self.helper.form_class = 'form-inline'
        self.helper.field_template = 'bootstrap3/layout/inline_field_with_label.html'
        self.helper.form_method = 'get'
        self.helper.layout = Layout(
            'structure',
            'year',
            InlineCheckboxes('state'),
        )


def structures_queryset(request):
    structures = Structure.objects.for_user(request.user)
    structures = structures.filter(Q(type=15) | Q(type__in=(10, 11), subtype=1))
    return structures.order_by('name')


class BookingFilter(django_filters.FilterSet):
    structure = django_filters.ModelChoiceFilter(label="Centre", queryset=structures_queryset, name='structure')
    year_choices = [(year, str(year)) for year in range(settings.NOW().year, 2015, -1)]
    year = django_filters.ChoiceFilter(label="Année", choices=year_choices, name='begin__year')
    state = django_filters.ModelMultipleChoiceFilter(label="Statut", queryset=BookingState.objects.all(),
                                                     widget=forms.CheckboxSelectMultiple)

    class Meta:
        model = Booking
        fields = ('structure', 'year', 'state')
        form = BookingFilterForm

    def __init__(self, data, *args, **kwargs):
        if data is None:
            data = QueryDict('state=3&state=4&state=5&state=6&state=7&state=9')
        super().__init__(data, *args, **kwargs)

    @property
    def qs(self):
        qs = super().qs.order_by('begin')
        qs = qs.select_related('state')
        qs = qs.prefetch_related('agreements', 'payments')
        return qs


class BookingItemFilterForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_class = 'form-inline'
        self.helper.field_template = 'bootstrap3/layout/inline_field_with_label.html'
        self.helper.form_method = 'get'
        self.helper.layout = Layout(
            'structure',
            InlineCheckboxes('state'),
        )


class BookingItemFilter(django_filters.FilterSet):
    structure = django_filters.ModelChoiceFilter(label="Centre", queryset=structures_queryset,
                                                 name='booking__structure')
    state = django_filters.ModelMultipleChoiceFilter(label="Statut", queryset=BookingState.objects.all(),
                                                     widget=forms.CheckboxSelectMultiple, name='booking__state')

    class Meta:
        model = BookingItem
        fields = ('structure', 'state')
        form = BookingItemFilterForm

    def __init__(self, data, *args, **kwargs):
        if data is None:
            data = QueryDict('state=3&state=4&state=5&state=6&state=7&state=9')
        super().__init__(data, *args, **kwargs)

    @property
    def qs(self):
        qs = super().qs.filter(begin__gte=settings.NOW().date()).select_related('booking', 'booking__state')
        return qs

from datetime import timedelta
from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.files import File
from django.db.models import Sum, Min, Max
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django.urls import reverse
from django.utils.text import slugify
from django.views.generic import TemplateView, DetailView, CreateView
from django_filters.views import FilterView
from os import unlink
from templated_docs import fill_template
from .filters import BookingFilter, BookingItemFilter, StatsFilter, CotisationsFilter
from .forms import BookingForm
from .models import Booking, BookingItem, Agreement


class HomeView(LoginRequiredMixin, TemplateView):
    template_name = 'booking/home.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        items = BookingItem.objects.for_user(self.request.user)
        potential_items = items.filter(booking__state__income=1)
        potential_incomes = [item.amount - item.amount_cot for item in potential_items]
        potential_overnights = [item.overnights for item in potential_items]
        context['potential_income'] = sum(filter(bool, potential_incomes))
        context['potential_overnights'] = sum(filter(bool, potential_overnights))
        confirmed_items = items.filter(booking__state__income__in=(2, 3))
        confirmed_incomes = [item.amount - item.amount_cot for item in confirmed_items]
        confirmed_overnights = [item.overnights for item in confirmed_items]
        context['confirmed_income'] = sum(filter(bool, confirmed_incomes))
        context['confirmed_overnights'] = sum(filter(bool, confirmed_overnights))
        context['total_income'] = context['potential_income'] + context['confirmed_income']
        context['total_overnights'] = context['potential_overnights'] + context['confirmed_overnights']
        return context


class BookingListView(LoginRequiredMixin, FilterView):
    template_name = 'booking/booking_list.html'
    filterset_class = BookingFilter

    def get_queryset(self):
        return Booking.objects.for_user(self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['overnights'] = sum([booking.overnights for booking in self.object_list if booking.overnights])
        context['headcount'] = sum([booking.headcount for booking in self.object_list if booking.headcount])
        context['amount'] = sum([booking.amount for booking in self.object_list if booking.amount])
        context['balance'] = sum([booking.balance for booking in self.object_list if booking.balance])
        return context


class BookingDetailView(LoginRequiredMixin, DetailView):
    model = Booking

    def render_to_response(self, context):
        if not self.object.structure.nominated(self.request.user):
            return HttpResponseForbidden()
        return super().render_to_response(context)


class BookingCreateView(PermissionRequiredMixin, CreateView):
    model = Booking
    form_class = BookingForm
    permission_required = 'booking.create'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs


class CreateAgreementView(LoginRequiredMixin, DetailView):
    model = Booking

    def render_to_response(self, context):
        if not self.object.structure.nominated(self.request.user):
            return HttpResponseForbidden()
        year = self.object.items.earliest('begin').begin.year
        try:
            order = Agreement.objects.filter(date__year=year).latest('order').order + 1
        except Agreement.DoesNotExist:
            order = 1
        agreement = Agreement.objects.create(date=settings.NOW().date(), order=order, booking=self.object)
        context['agreement'] = agreement
        for ext in ('odt', 'pdf'):
            filename = fill_template('booking/agreement.odt', context, output_format=ext)
            visible_filename = "Convention_{number}_{title}.{ext}".format(number=agreement.number(), ext=ext,
                                                                          title=slugify(self.object.title))
            f = open(filename, 'rb')
            getattr(agreement, ext).save(visible_filename, File(f))
            f.close()
            unlink(filename)
        return HttpResponseRedirect(reverse('booking:booking_detail', kwargs={'pk': self.object.pk}))


class OccupancyView(LoginRequiredMixin, FilterView):
    template_name = 'booking/occupancy.html'
    filterset_class = BookingItemFilter

    def occupancy_for(self, day, product):
        items = self.object_list.filter(begin__lte=day, end__gt=day, product=product)
        items = items.filter(headcount__isnull=False)
        items = items.order_by('booking__title')
        items = items.values('booking__title', 'booking__state__color')
        items = items.annotate(headcount=Sum('headcount'))
        return len(items), sum([item['headcount'] for item in items]), items

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        occupancy = []
        range_qs = self.object_list.filter(end__gte=settings.NOW())
        range_qs = range_qs.aggregate(begin=Min('begin'), end=Max('end'))
        if range_qs['begin'] and range_qs['end']:
            begin = max(range_qs['begin'], settings.NOW().date())
            end = range_qs['end']
            for i in range((end - begin).days + 1):
                day = begin + timedelta(days=i)
                occupancy.append((day, ) + self.occupancy_for(day, 2) + self.occupancy_for(day, 1))
        context['occupancy'] = occupancy
        return context


class StatsView(LoginRequiredMixin, TemplateView):
    template_name = 'booking/stats.html'

    def get_context_data(self, **kwargs):
        filter = StatsFilter(self.request.GET or None, request=self.request,
                             queryset=Booking.objects.for_user(self.request.user))
        items = BookingItem.objects.filter(booking__in=filter.qs)
        kwargs['filter'] = filter
        kwargs['stats'] = {
            'headcount': sum([item.headcount for item in items if item.headcount]),
            'headcount_cot': sum([item.headcount for item in items if item.headcount and item.cotisation]),
            'overnights': sum([item.overnights for item in items if item.overnights]),
            'overnights_cot': sum([item.overnights for item in items if item.overnights and item.cotisation]),
            'amount_hosting': sum([item.amount - item.amount_cot for item in items if item.product in (1, 2, 5)]),
            'amount_cot': sum([item.overnights for item in items if item.overnights and item.cotisation]),
            'amount_renting': sum([item.amount for item in items if item.product == 3]),
            'amount_recharge': sum([item.amount for item in items if item.product == 4]),
            'amount': sum([item.amount for item in items]),
        }
        if kwargs['stats']['overnights']:
            kwargs['stats']['overnight_cost'] = kwargs['stats']['amount_hosting'] / kwargs['stats']['overnights']

        stats = (
            ('stats_village', items.filter(product__in=(2, 5))),
            ('stats_terrain', items.filter(product=1)),
            ('stats_q1', items.filter(begin__month__lte=3)),
            ('stats_q2', items.filter(begin__month__gte=4, begin__month__lte=6)),
            ('stats_q3', items.filter(begin__month__gte=7, begin__month__lte=9)),
            ('stats_q4', items.filter(begin__month__gte=10)),
        )
        for (name, subitems) in stats:
            kwargs[name] = {
                'headcount': sum([item.headcount for item in subitems if item.headcount]),
                'overnights': sum([item.overnights for item in subitems if item.overnights]),
                'amount_hosting': sum([item.amount - item.amount_cot
                                       for item in subitems if item.product in (1, 2, 5)]),
                'amount_cot': sum([item.overnights for item in subitems if item.overnights]),
                'amount_renting': sum([item.amount for item in subitems if item.product == 3]),
                'amount_recharge': sum([item.amount for item in subitems if item.product == 4]),
                'amount': sum([item.amount for item in subitems]),
            }
            if kwargs['stats']['overnights']:
                kwargs[name]['overnights_rate'] = (100 * kwargs[name]['overnights'] / kwargs['stats']['overnights'])
            if kwargs['stats']['amount_hosting']:
                kwargs[name]['amount_hosting_rate'] = (100 * kwargs[name]['amount_hosting'] /
                                                       kwargs['stats']['amount_hosting'])
            if kwargs[name]['overnights']:
                kwargs[name]['overnight_cost'] = (kwargs[name]['amount_hosting'] / kwargs[name]['overnights'])

        return kwargs


class CotisationsView(LoginRequiredMixin, FilterView):
    template_name = 'booking/cotisations.html'
    filterset_class = CotisationsFilter

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if 'year' in self.filterset.data:
            year = int(self.filterset.data['year'])
            context['date'] = "{}/{}".format(year, year + 1)
        context['headcount'] = sum(item.headcount for item in self.object_list)
        context['amount_cot'] = sum(item.amount_cot for item in self.object_list)
        return context


class BookingGoogleSyncView(LoginRequiredMixin, DetailView):
    model = Booking

    def render_to_response(self, context, **response_kwargs):
        self.object.sync_calendar()
        return HttpResponseRedirect(reverse('booking:booking_list'))

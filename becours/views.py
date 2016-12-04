from django.db.models import Sum, F
from django.views.generic.base import TemplateView
from becours.models import Group, Headcount


class StatsView(TemplateView):
    template_name = 'becours/stats.html'

    def get_context_data(self, **kwargs):
        kwargs['stats'] = Group.objects.aggregate(
            number=Sum('number'),
            overnights=Sum('overnights'),
            hosting_cost=Sum('hosting_cost'),
            coop_cost=Sum('coop_cost'),
            additional_cost=Sum('additional_cost'),
            cost=Sum('cost')
        )
        kwargs['stats']['overnight_cost'] = kwargs['stats']['hosting_cost'] / kwargs['stats']['overnights']
        kwargs['stats_eedf'] = Group.objects.filter(type=1).aggregate(
            number=Sum('number'),
            overnights=Sum('overnights'),
            hosting_cost=Sum('hosting_cost'),
            coop_cost=Sum('coop_cost'),
            additional_cost=Sum('additional_cost'),
            cost=Sum('cost')
        )
        kwargs['stats_eedf']['overnights_rate'] = 100 * kwargs['stats_eedf']['overnights'] / kwargs['stats']['overnights']
        kwargs['stats_eedf']['hosting_cost_rate'] = 100 * kwargs['stats_eedf']['hosting_cost'] / kwargs['stats']['hosting_cost']
        kwargs['stats_eedf']['overnight_cost'] = kwargs['stats_eedf']['hosting_cost'] / kwargs['stats_eedf']['overnights']
        kwargs['stats_ext'] = Group.objects.exclude(type=1).aggregate(
            number=Sum('number'),
            overnights=Sum('overnights'),
            hosting_cost=Sum('hosting_cost'),
            coop_cost=Sum('coop_cost'),
            additional_cost=Sum('additional_cost'),
            cost=Sum('cost')
        )
        kwargs['stats_ext']['overnights_rate'] = 100 * kwargs['stats_ext']['overnights'] / kwargs['stats']['overnights']
        kwargs['stats_ext']['hosting_cost_rate'] = 100 * kwargs['stats_ext']['hosting_cost'] / kwargs['stats']['hosting_cost']
        kwargs['stats_ext']['overnight_cost'] = kwargs['stats_ext']['hosting_cost'] / kwargs['stats_ext']['overnights']
        kwargs['stats_village'] = Headcount.objects.filter(comfort=2).aggregate(
            overnights=Sum('overnights'),
            hosting_cost=Sum('hosting_cost')
        )
        kwargs['stats_village']['overnights_rate'] = 100 * kwargs['stats_village']['overnights'] / kwargs['stats']['overnights']
        kwargs['stats_village']['hosting_cost_rate'] = 100 * kwargs['stats_village']['hosting_cost'] / kwargs['stats']['hosting_cost']
        kwargs['stats_village']['overnight_cost'] = kwargs['stats_village']['hosting_cost'] / kwargs['stats_village']['overnights']
        kwargs['stats_terrain'] = Headcount.objects.filter(comfort=1).aggregate(
            overnights=Sum('overnights'),
            hosting_cost=Sum('hosting_cost')
        )
        kwargs['stats_terrain']['overnights_rate'] = 100 * kwargs['stats_terrain']['overnights'] / kwargs['stats']['overnights']
        kwargs['stats_terrain']['hosting_cost_rate'] = 100 * kwargs['stats_terrain']['hosting_cost'] / kwargs['stats']['hosting_cost']
        kwargs['stats_terrain']['overnight_cost'] = kwargs['stats_terrain']['hosting_cost'] / kwargs['stats_terrain']['overnights']
        kwargs['stats_village_eedf'] = Headcount.objects.filter(group__type=1, comfort=2).aggregate(
            overnights=Sum('overnights'),
            hosting_cost=Sum('hosting_cost')
        )
        kwargs['stats_village_eedf']['overnights_rate'] = 100 * kwargs['stats_village_eedf']['overnights'] / kwargs['stats']['overnights']
        kwargs['stats_village_eedf']['hosting_cost_rate'] = 100 * kwargs['stats_village_eedf']['hosting_cost'] / kwargs['stats']['hosting_cost']
        kwargs['stats_village_eedf']['overnight_cost'] = kwargs['stats_village_eedf']['hosting_cost'] / kwargs['stats_village_eedf']['overnights']
        kwargs['stats_village_ext'] = Headcount.objects.exclude(group__type=1).filter(comfort=2).aggregate(
            overnights=Sum('overnights'),
            hosting_cost=Sum('hosting_cost')
        )
        kwargs['stats_village_ext']['overnights_rate'] = 100 * kwargs['stats_village_ext']['overnights'] / kwargs['stats']['overnights']
        kwargs['stats_village_ext']['hosting_cost_rate'] = 100 * kwargs['stats_village_ext']['hosting_cost'] / kwargs['stats']['hosting_cost']
        kwargs['stats_village_ext']['overnight_cost'] = kwargs['stats_village_ext']['hosting_cost'] / kwargs['stats_village_ext']['overnights']
        kwargs['stats_terrain_eedf'] = Headcount.objects.filter(group__type=1, comfort=1).aggregate(
            overnights=Sum('overnights'),
            hosting_cost=Sum('hosting_cost')
        )
        kwargs['stats_terrain_eedf']['overnights_rate'] = 100 * kwargs['stats_terrain_eedf']['overnights'] / kwargs['stats']['overnights']
        kwargs['stats_terrain_eedf']['hosting_cost_rate'] = 100 * kwargs['stats_terrain_eedf']['hosting_cost'] / kwargs['stats']['hosting_cost']
        kwargs['stats_terrain_eedf']['overnight_cost'] = kwargs['stats_terrain_eedf']['hosting_cost'] / kwargs['stats_terrain_eedf']['overnights']
        kwargs['stats_terrain_ext'] = Headcount.objects.exclude(group__type=1).filter(comfort=1).aggregate(
            overnights=Sum('overnights'),
            hosting_cost=Sum('hosting_cost')
        )
        kwargs['stats_terrain_ext']['overnights_rate'] = 100 * kwargs['stats_terrain_ext']['overnights'] / kwargs['stats']['overnights']
        kwargs['stats_terrain_ext']['hosting_cost_rate'] = 100 * kwargs['stats_terrain_ext']['hosting_cost'] / kwargs['stats']['hosting_cost']
        kwargs['stats_terrain_ext']['overnight_cost'] = kwargs['stats_terrain_ext']['hosting_cost'] / kwargs['stats_terrain_ext']['overnights']
        kwargs['stats_ete'] = Headcount.objects.filter(end__gte='2016-07-01', begin__lte='2016-08-31').aggregate(
            overnights=Sum('overnights'),
            hosting_cost=Sum('hosting_cost')
        )
        kwargs['stats_ete']['overnights_rate'] = 100 * kwargs['stats_ete']['overnights'] / kwargs['stats']['overnights']
        kwargs['stats_ete']['hosting_cost_rate'] = 100 * kwargs['stats_ete']['hosting_cost'] / kwargs['stats']['hosting_cost']
        kwargs['stats_ete']['overnight_cost'] = kwargs['stats_ete']['hosting_cost'] / kwargs['stats_ete']['overnights']
        kwargs['stats_avr'] = Headcount.objects.filter(end__gte='2016-04-16', begin__lte='2016-05-01').aggregate(
            overnights=Sum('overnights'),
            hosting_cost=Sum('hosting_cost')
        )
        kwargs['stats_avr']['overnights_rate'] = 100 * kwargs['stats_avr']['overnights'] / kwargs['stats']['overnights']
        kwargs['stats_avr']['hosting_cost_rate'] = 100 * kwargs['stats_avr']['hosting_cost'] / kwargs['stats']['hosting_cost']
        kwargs['stats_avr']['overnight_cost'] = kwargs['stats_avr']['hosting_cost'] / kwargs['stats_avr']['overnights']
        kwargs['stats_oct'] = Headcount.objects.filter(end__gte='2016-10-20', begin__lte='2016-11-02').aggregate(
            overnights=Sum('overnights'),
            hosting_cost=Sum('hosting_cost')
        )
        kwargs['stats_oct']['overnights_rate'] = 100 * kwargs['stats_oct']['overnights'] / kwargs['stats']['overnights']
        kwargs['stats_oct']['hosting_cost_rate'] = 100 * kwargs['stats_oct']['hosting_cost'] / kwargs['stats']['hosting_cost']
        kwargs['stats_oct']['overnight_cost'] = kwargs['stats_oct']['hosting_cost'] / kwargs['stats_oct']['overnights']
        return kwargs

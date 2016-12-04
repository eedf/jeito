from django.db.models import Sum
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

        GROUP_STATS = (
            ('stats_eedf', Group.objects.filter(type=1)),
            ('stats_ext', Group.objects.exclude(type=1)),
        )
        for (name, groups) in GROUP_STATS:
            kwargs[name] = groups.aggregate(
                number=Sum('number'),
                overnights=Sum('overnights'),
                hosting_cost=Sum('hosting_cost'),
                coop_cost=Sum('coop_cost'),
                additional_cost=Sum('additional_cost'),
                cost=Sum('cost')
            )
            kwargs[name]['overnights_rate'] = (100 * kwargs[name]['overnights'] / kwargs['stats']['overnights'])
            kwargs[name]['hosting_cost_rate'] = (100 * kwargs[name]['hosting_cost'] / kwargs['stats']['hosting_cost'])
            kwargs[name]['overnight_cost'] = (kwargs[name]['hosting_cost'] / kwargs[name]['overnights'])

        HEADCOUNT_STATS = (
            ('stats_village', Headcount.objects.filter(comfort=2)),
            ('stats_terrain', Headcount.objects.filter(comfort=1)),
            ('stats_village_eedf', Headcount.objects.filter(group__type=1, comfort=2)),
            ('stats_village_ext', Headcount.objects.exclude(group__type=1).filter(comfort=2)),
            ('stats_terrain_eedf', Headcount.objects.filter(group__type=1, comfort=1)),
            ('stats_terrain_ext', Headcount.objects.exclude(group__type=1).filter(comfort=1)),
            ('stats_ete', Headcount.objects.filter(end__gte='2016-07-01', begin__lte='2016-08-31')),
            ('stats_avr', Headcount.objects.filter(end__gte='2016-04-16', begin__lte='2016-05-01')),
            ('stats_oct', Headcount.objects.filter(end__gte='2016-10-20', begin__lte='2016-11-02')),
        )
        for (name, headcounts) in HEADCOUNT_STATS:
            kwargs[name] = headcounts.aggregate(
                overnights=Sum('overnights'),
                hosting_cost=Sum('hosting_cost')
            )
            kwargs[name]['overnights_rate'] = (100 * kwargs[name]['overnights'] / kwargs['stats']['overnights'])
            kwargs[name]['hosting_cost_rate'] = (100 * kwargs[name]['hosting_cost'] / kwargs['stats']['hosting_cost'])
            kwargs[name]['overnight_cost'] = (kwargs[name]['hosting_cost'] / kwargs[name]['overnights'])
        return kwargs

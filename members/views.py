from collections import OrderedDict
from datetime import date, timedelta
from django.contrib.auth.mixins import LoginRequiredMixin
from django.conf import settings
from django.db.models import Count, F, ExpressionWrapper, DecimalField
from django.http import JsonResponse
from django.utils.formats import date_format
from django.views.generic import View, TemplateView
import json
from .filters import AdhesionFilter
from .forms import AdhesionsForm
from .models import Adhesion, Structure, Function, Rate
from .utils import current_season


# TODO: use AdhesionFilter
class AdhesionsJsonView(LoginRequiredMixin, View):
    SVN_NUMBERS = ('0300000200', '0500000100', '1900140100')
    CPN_NUMBERS = tuple(a + b for a, b in zip(('18000002', '14005719', '27000006', '17000003', '27000005'),
                                              ('00', '01', '02', '03', '04')))

    def serie(self, season, GET):
        self.today = (settings.NOW() - timedelta(days=1)).date()
        start = date(season - 1, 9, 1)
        end = min(date(season, 8, 31), self.today)
        qs = Adhesion.objects.filter(season=season)
        if GET['sector'] == '1':
            qs = qs.exclude(structure__number__in=self.SVN_NUMBERS + self.CPN_NUMBERS)
        elif GET['sector'] == '2':
            qs = qs.filter(structure__number__in=self.SVN_NUMBERS)
        elif GET['sector'] == '3':
            qs = qs.filter(structure__number__in=self.CPN_NUMBERS)
        if GET['units'] == '99':
            qs = qs.exclude(structure__type__in=(1, 2, 7, 13))
        elif GET['units']:
            qs = qs.filter(structure__type=GET['units'])
        if GET['function']:
            qs = qs.filter(function__category=GET['function'])
        if GET['rate']:
            qs = qs.filter(rate__category=GET['rate'])
        qs = qs.order_by('-date').values('date').annotate(headcount=Count('id'))
        qs = list(qs)
        data = OrderedDict()
        dates = [start + timedelta(days=n) for n in
                 range((end - start).days + 1)]
        acc = 0
        for d in dates:
            if qs and qs[-1]['date'] == d:
                acc += qs.pop()['headcount']
            if d.month == 2 and d.day == 29:
                continue
            data[d] = acc
        return data

    def get(self, request):
        season = int(self.request.GET['season'])
        reference = season - 1
        data = self.serie(season, self.request.GET)
        ref_data = self.serie(reference, self.request.GET)
        date_max = max(data.keys())
        ref_date_max = date_max.replace(year=reference if date_max.month <= 8 else reference - 1,
                                        month=date_max.month, day=date_max.day)
        date1 = ref_date_max.strftime('%d/%m/%Y')
        date2 = date_max.strftime('%d/%m/%Y')
        nb1 = ref_data[ref_date_max]
        nb2 = data[date_max]
        diff = nb2 - nb1
        if nb1:
            percent = 100 * diff / nb1
            comment = """Au <strong>{}</strong> : <strong>{}</strong> adhérents<br>
                         Au <strong>{}</strong> : <strong>{}</strong> adhérents,
                         c'est-à-dire <strong>{:+d}</strong> adhérents
                         (<strong>{:+0.1f} %</strong>)
                      """.format(date1, nb1, date2, nb2, diff, percent)
        else:
            comment = """Au <strong>{}</strong> : <strong>{}</strong> adhérents
                      """.format(date2, nb2)
        data = {
            'labels': [date_format(x, 'b') if x.day == 1 else '' for x in ref_data.keys()],
            'series': [
                list(ref_data.values()),
                list(data.values()),
            ],
            'comment': comment,
        }
        return JsonResponse(data)


class AdhesionsView(LoginRequiredMixin, TemplateView):
    def get_template_names(self):
        if 'print' in self.request.GET:
            return 'members/adhesions_print.html'
        else:
            return 'members/adhesions.html'

    def get_context_data(self, **kwargs):
        season = self.request.GET.get('season', current_season())
        sector = self.request.GET.get('sector', 0)
        branch = self.request.GET.get('units', 0)
        initial = self.request.GET.dict()
        initial.update({
            'season': season,
            'sector': sector,
            'units': branch,
        })
        form = AdhesionsForm(initial=initial)
        context = super().get_context_data(**kwargs)
        context['form'] = form
        context.update(initial)
        return context


class TableauAmountView(LoginRequiredMixin, TemplateView):
    template_name = 'members/tableau_amount.html'

    def get_context_data(self, **kwargs):
        filter = AdhesionFilter(self.request.GET)
        qs = filter.qs.values('rate__name', 'rate__rate')
        qs = qs.annotate(headcount=Count('id'))
        qs = qs.annotate(amount=ExpressionWrapper(Count('id') * F('rate__rate'), output_field=DecimalField()))
        qs = qs.order_by('-amount')
        context = {
            'filter': filter,
            'date': filter.date.strftime('%d/%m/%Y'),
            'data': qs,
            'total_headcount': sum([obj['headcount'] or 0 for obj in qs]),
            'total_amount': sum([obj['amount'] or 0 for obj in qs]),
        }
        return context


class TableauView(LoginRequiredMixin, TemplateView):
    template_name = 'members/tableau.html'

    def format_diff(self, row):
        diff = row[1] - row[0]
        if diff > 0:
            return "+ {}".format(diff)
        elif diff == 0:
            return "="
        else:
            return "- {}".format(-diff)

    def format_percent(self, row):
        diff = row[1] - row[0]
        if diff == 0:
            return "="
        elif not row[0]:
            return "∞"
        elif diff > 0:
            return "+ {:0.1f} %".format(100 * diff / row[0])
        else:
            return "- {:0.1f} %".format(-100 * diff / row[0])

    def aggregate(self, qs):
        qs = qs.values(*self.values).annotate(headcount=Count('id'))
        qs = qs.order_by('-headcount')
        return qs

    def graph_label(self, key, values, total):
        if values[1] * 50 < total[1]:
            return None
        if not total[1]:
            return key
        return "{} ({:0.1f}%)".format(key, 100 * values[1] / total[1])

    def get_context_data(self, **kwargs):
        filter = AdhesionFilter(self.request.GET)
        ref_filter = AdhesionFilter(self.request.GET, ref=True)
        data = OrderedDict()
        total = [0, 0]
        for i, qs in ((1, filter.qs), (0, ref_filter.qs)):
            qs = self.aggregate(qs)
            for obj in qs:
                data.setdefault(self.row_key(obj), [0, 0])[i] = obj['headcount']
                total[i] += obj['headcount']
        graph = {
            'labels': [self.graph_label(key, values, total) for key, values in data.items()],
            'series': [values[1] for values in data.values()]
        }
        data['TOTAL'] = total
        for row in data.values():
            row.append(self.format_diff(row))
            row.append(self.format_percent(row))
        context = {
            'title': self.title,
            'filter': filter,
            'header': (
                "Au {}".format(ref_filter.date.strftime('%d/%m/%Y')),
                "Au {}".format(filter.date.strftime('%d/%m/%Y')),
                "Variation",
                "Variation %",
            ),
            'data': data,
            'graph': json.dumps(graph),
        }
        return context


class TableauStructureTypeView(TableauView):
    values = ('structure__type', 'structure__subtype')
    title = "type de structure"

    def row_key(self, obj):
        type = dict(Structure.TYPE_CHOICES)[obj['structure__type']]
        if obj['structure__subtype']:
            type += " (" + dict(Structure.SUBTYPE_CHOICES)[obj['structure__subtype']] + ")"
        return type


class TableauStructureView(TableauView):
    values = ('structure__name', )
    title = "structure"

    def row_key(self, obj):
        return obj['structure__name']


class TableauFunctionsView(TableauView):
    values = ('function__category', )
    title = "fonction"

    def row_key(self, obj):
        return dict(Function.CATEGORY_CHOICES)[obj['function__category']]


class TableauRateView(TableauView):
    values = ('rate__category', )
    title = "tarif"

    def row_key(self, obj):
        if obj['rate__category'] is None:
            return "Autre"
        return dict(Rate.CATEGORY_CHOICES)[obj['rate__category']]


class TableauRegionsView(TableauView):
    values = ('region', )
    title = "région"

    def aggregate(self, qs):
        regions = Structure.objects.filter(type=6).order_by('name')
        res = []
        for region in regions:
            headcount = qs.filter(structure__in=region.get_descendants(include_self=True)).count()
            res.append({'region': region, 'headcount': headcount})
        res.sort(key=lambda obj: obj['headcount'], reverse=True)
        return res

    def row_key(self, obj):
        return obj['region'].name.replace('EEDF ', '')


# TODO: calcule le prix moyen de la cotisation (avant et après déduction)
class TranchesView(TableauView):
    values = ('rate__bracket', )
    title = "tranche d'imposition"

    def aggregate(self, qs):
        qs = super().aggregate(qs)
        qs = qs.filter(rate__category=1)
        return qs

    def row_key(self, obj):
        return obj['rate__bracket']

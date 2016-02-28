from collections import OrderedDict
from datetime import date
from django.db import connection
from django.db.models import Count
from django.http import JsonResponse
from django.utils.formats import date_format
from django.utils.timezone import now
from django.views.generic import View, TemplateView
from .forms import AdhesionsForm
from .models import Adhesion, Structure
from .utils import current_season


class AdhesionsJsonView(View):
    def serie(self, season):
        self.today = now().date()
        start = date(season - 1, 9, 1)
        end = min(date(season, 8, 31), self.today)
        sql = '''
            SELECT date, SUM(COUNT(members_structure.id)) OVER (ORDER BY date)
            FROM generate_series(%s::date, %s::date, '1 day'::interval) AS date
            LEFT JOIN members_adhesion USING (date)
            LEFT JOIN members_structure ON (members_structure.id = structure_id AND (subtype != 4 OR subtype IS NULL))
            GROUP BY date
            ORDER BY date'''
        params = [start, end]
        cursor = connection.cursor()
        cursor.execute(sql, params)
        return cursor.fetchall()

    def get(self, request):
        season = int(self.request.GET['season'])
        reference = int(self.request.GET.get('reference', '0')) or season - 1
        result = self.serie(int(season))
        ref_result = self.serie(int(reference))
        cmp_idx = min(len(result), len(ref_result)) - 1
        date1 = ref_result[cmp_idx][0].strftime('%d/%m/%Y')
        date2 = result[-1][0].strftime('%d/%m/%Y')
        nb1 = ref_result[cmp_idx][1]
        nb2 = result[-1][1]
        diff = nb2 - nb1
        if nb1:
            percent = 100 * diff / nb1
            comment = """Au <strong>{}</strong> : <strong>{}</strong> adhérents<br>
                         Au <strong>{}</strong> : <strong>{}</strong> adhérents,
                         c'est-à-dire <strong>{:+f}</strong> adhérents
                         (<strong>{:+0.1f} %</strong>)
                      """.format(date1, nb1, date2, nb2, diff, percent)
        else:
            comment = """Au <strong>{}</strong> : <strong>{}</strong> adhérents
                      """.format(date2, nb2)
        data = {
            'labels': [date_format(x[0], 'b') if x[0].day == 1 else '' for x in ref_result],
            'series': [
                [x[1] for x in ref_result],
                [x[1] for x in result],
            ],
            'comment': comment,
        }
        return JsonResponse(data)


class AdhesionsView(TemplateView):
    template_name = 'members/adhesions.html'

    def get_context_data(self, **kwargs):
        season = self.request.GET.get('season', current_season())
        reference = self.request.GET.get('reference')
        initial = self.request.GET.dict()
        initial.update({
            'season': season,
            'reference': reference,
        })
        form = AdhesionsForm(initial=initial)
        context = super().get_context_data(**kwargs)
        context['form'] = form
        context.update(initial)
        return context


class TranchesJsonView(View):

    def get(self, request):
        qs = Adhesion.objects.filter(season=2016).exclude(rate__bracket="")
        qs1 = qs.order_by('rate__bracket')
        qs1 = qs1.values('rate__bracket')
        qs1 = qs1.annotate(n=Count('id'))
        qs2 = qs.values('rate__name', 'rate__rate', 'rate__rate_after_tax_ex')
        qs2 = qs2.annotate(n=Count('id'))
        total1 = sum(x['n'] for x in qs1)
        total2 = sum(x['n'] for x in qs2)
        assert total1 == total2
        if qs.filter(rate__rate=None).exists():
            comment = "Données manquantes pour calculer la cotisation moyenne"
        else:
            average_price = sum([x['n'] * x['rate__rate'] for x in qs2]) / total2
            comment = "Cotisation moyenne : <strong>{:0.02f} €</strong>".format(float(average_price))
        if qs.filter(rate__rate_after_tax_ex=None).exists():
            comment += " (données manquantes pour calculer la cotisation moyenne après défiscalisation)"
        else:
            average_price_after_tax_ex = sum([x['n'] * x['rate__rate_after_tax_ex'] for x in qs2]) / total2
            comment += " ({:0.02f} € après défiscalisation)".format(float(average_price_after_tax_ex))
        data = {
            'labels': [x['rate__bracket'] + ' (%0.0f %%)' % (100 * x['n'] / total1) for x in qs1],
            'series': [x['n'] for x in qs1],
            'comment': comment,
        }
        return JsonResponse(data)


class TranchesView(TemplateView):
    template_name = 'members/tranches.html'


class TableauRegionsView(TemplateView):
    template_name = 'members/tableau_regions.html'

    def set_data(self, season, end):
        for region in self.regions:
            structures = region.get_descendants(include_self=True)
            adhesions = Adhesion.objects.filter(structure__in=structures, season=season, date__lte=end)
            adhesions = adhesions.exclude(structure__subtype=4)
            count = adhesions.count()
            self.data.setdefault(region.name, OrderedDict())[season] = count
        total_regions = sum([self.data[region.name][season] for region in self.regions])
        self.data.setdefault('<b>REGIONS</b>', OrderedDict())[season] = total_regions
        structures = Structure.objects.filter(number__in=('0000100000', '0000200000'))
        structures = structures.get_descendants(include_self=True)
        count = Adhesion.objects.filter(structure__in=structures, season=season, date__lte=end).count()
        self.data.setdefault('<b>SIEGE NATIONAL</b>', OrderedDict())[season] = count
        services = Structure.objects.filter(subtype=4).order_by('name')
        for service in services:
            adhesions = Adhesion.objects.filter(structure=service, season=season, date__lte=end)
            count = adhesions.count()
            self.data.setdefault(service.name, OrderedDict())[season] = count
        count = Adhesion.objects.filter(structure__subtype=4, season=season, date__lte=end).count()
        self.data.setdefault('<b>SERVICES VACANCES</b>', OrderedDict())[season] = count
        total = Adhesion.objects.filter(season=season, date__lte=end).count()
        self.data.setdefault('<b>TOTAL</b>', OrderedDict())[season] = total
        count = self.data['<b>REGIONS</b>'][season]
        count += self.data['<b>SIEGE NATIONAL</b>'][season]
        count += self.data['<b>SERVICES VACANCES</b>'][season]
        assert count == total

    def get_context_data(self, **kwargs):
        season = int(self.request.GET.get('season', current_season()))
        reference = int(self.request.GET.get('reference', '0')) or season - 1
        end = min(date(season, 8, 31), now().date())
        self.regions = Structure.objects.filter(type=6).order_by('name')
        self.data = OrderedDict()
        self.set_data(reference, end.replace(year=reference))
        self.set_data(season, end)
        for key, val in self.data.items():
            diff = val[season] - val[reference]
            if diff > 0:
                val['diff'] = "+ {}".format(diff)
            elif diff == 0:
                val['diff'] = "="
            else:
                val['diff'] = "- {}".format(-diff)
            if diff == 0:
                val['percent'] = "="
            elif not val[reference]:
                val['percent'] = "∞"
            elif diff > 0:
                val['percent'] = "+ {:0.1f} %".format(100 * diff / val[reference])
            else:
                val['percent'] = "- {:0.1f} %".format(-100 * diff / val[reference])
        context = {
            'seasons': [
                "{}/{}".format(reference - 1, reference),
                "{}/{}".format(season - 1, season),
                "Variation",
                "Variation %",
            ],
            'data': self.data,
        }
        return context


class TableauFunctionsView(TemplateView):
    template_name = 'members/tableau_functions.html'

    def set_data(self, season, end):
        all_adhesions = Adhesion.objects.filter(season=season)
        all_adhesions = all_adhesions.filter(date__lte=end)
        all_adhesions = all_adhesions.exclude(structure__subtype=4)
        for function in self.functions:
            count_func = all_adhesions.filter(function__name_m=function).count()
            self.data.setdefault(function, OrderedDict())[season] = count_func
        count_all = all_adhesions.count()
        count_others = count_all - sum([self.data[function][season] for function in self.functions])
        self.data.setdefault('Autre', OrderedDict())[season] = count_others
        self.data.setdefault('<b>TOTAL</b>', OrderedDict())[season] = count_all

    def get_context_data(self, **kwargs):
        season = self.request.GET.get('season', current_season())
        self.functions = (
            "Stagiaire",
            "Lutin",
            "Louveteau",
            "Eclaireur",
            "Ainé",
            "Participant activité",
            "Ami",
            "Parent",
            "Nomade",
            "Service civique",
        )
        season = int(self.request.GET.get('season', current_season()))
        reference = int(self.request.GET.get('reference', '0')) or season - 1
        end = min(date(season, 8, 31), now().date())
        self.data = OrderedDict()
        self.set_data(reference, end.replace(year=reference))
        self.set_data(season, end)
        for key, val in self.data.items():
            diff = val[season] - val[reference]
            if diff > 0:
                val['diff'] = "+ {}".format(diff)
            elif diff == 0:
                val['diff'] = "="
            else:
                val['diff'] = "- {}".format(-diff)
            if diff == 0:
                val['percent'] = "="
            elif not val[reference]:
                val['percent'] = "∞"
            elif diff > 0:
                val['percent'] = "+ {:0.1f} %".format(100 * diff / val[reference])
            else:
                val['percent'] = "- {:0.1f} %".format(-100 * diff / val[reference])
        context = {
            'seasons': [
                "{}/{}".format(reference - 1, reference),
                "{}/{}".format(season - 1, season),
                "Variation",
                "Variation %",
            ],
            'data': self.data,
        }
        return context

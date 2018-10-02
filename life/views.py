from django.views.generic import ListView, CreateView
from .models import Report


class ReportListView(ListView):
    model = Report


class ReportCreateView(CreateView):
    model = Report
    fields = ('structure', 'date', 'location', 'nb_presents', 'nb_voters', 'representative', 'favour', 'against',
              'abstention', 'balance', 'budget', 'delegate', 'alternate', 'responsible', 'treasurer',
              'responsible_validation', 'representative_validation', 'comments_activity_report', 'comments_finances',
              'comments_national', 'comments_regional', 'comments_problems', 'team')

from django.views.generic import ListView, DetailView
from .models import Report


class ReportListView(ListView):
    model = Report


class ReportDetailView(DetailView):
    model = Report

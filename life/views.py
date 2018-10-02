from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView
from .forms import ReportForm
from .models import Report


class ReportListView(LoginRequiredMixin, ListView):
    model = Report


class ReportCreateView(LoginRequiredMixin, CreateView):
    model = Report
    form_class = ReportForm

from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from .widget import widgets


class DashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'dashboard/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['widget_templates'] = [widget.template_name for widget in widgets]
        for widget in widgets:
            context.update(widget.get_context_data())
        return context

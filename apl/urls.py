from django.conf.urls import url
from .views import ReportListView, ReportDetailView


urlpatterns = [
    url(r'^$', ReportListView.as_view(), name='report_list'),
    url(r'^(?P<pk>\d+)/$', ReportDetailView.as_view(), name='report_detail'),
]

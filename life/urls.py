from django.conf.urls import url, include
from . import views

urlpatterns = [
    url(r'^', include('core.urls')),
    url(r'^reports/$', views.ReportListView.as_view(), name='report_list'),
    url(r'^reports/create/$', views.ReportCreateView.as_view(), name='report_create'),
]

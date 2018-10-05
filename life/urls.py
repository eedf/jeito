from django.conf.urls import url
from . import views

app_name = 'life'

urlpatterns = [
    url(r'^reports/$', views.ReportListView.as_view(), name='report_list'),
    url(r'^reports/create/$', views.ReportCreateView.as_view(), name='report_create'),
]

from django.conf.urls import url
from . import views


app_name = 'becours'

urlpatterns = [
    url(r'^$', views.HomeView.as_view(), name='list'),
    url(r'^stats/$', views.StatsView.as_view(), name='stats'),
    url(r'^estimate/(?P<pk>\d+)/$', views.EstimateView.as_view(), name='estimate'),
]

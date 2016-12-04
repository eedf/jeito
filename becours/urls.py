from django.conf.urls import url
from . import views


app_name = 'becours'

urlpatterns = [
    url(r'^stats/$', views.StatsView.as_view(), name='stats'),
]

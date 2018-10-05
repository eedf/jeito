from django.conf.urls import url
from .views import DashboardView

app_name = 'dashboard'

urlpatterns = [
    url(r'^$', DashboardView.as_view(), name='dashboard'),
]

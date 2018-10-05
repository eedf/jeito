from django.conf.urls import url
from . import views


urlpatterns = [
    url(r'^$', views.HomeView.as_view(), name='home'),
    url(r'^list/$', views.BookingListView.as_view(), name='booking_list'),
    url(r'^detail/(?P<pk>\d+)/$', views.BookingDetailView.as_view(), name='booking_detail'),
    url(r'^create/$', views.BookingCreateView.as_view(), name='create'),
    url(r'^google_sync/(?P<pk>\d+)/$', views.BookingGoogleSyncView.as_view(), name='booking_google_sync'),
    url(r'^occupancy/$', views.OccupancyView.as_view(), name='occupancy'),
    url(r'^stats/$', views.StatsView.as_view(), name='stats'),
    url(r'^cotisations/$', views.CotisationsView.as_view(), name='cotisations'),
]

from django.conf.urls import url
from .views import HomeView, BookingListView, BookingDetailView, CreateAgreementView, OccupancyView, StatsView


urlpatterns = [
    url(r'^$', HomeView.as_view(), name='home'),
    url(r'^list/$', BookingListView.as_view(), name='booking_list'),
    url(r'^detail/(?P<pk>\d+)/$', BookingDetailView.as_view(), name='booking_detail'),
    url(r'^create_agreement/(?P<pk>\d+)/$', CreateAgreementView.as_view(), name='create_agreement'),
    url(r'^occupancy/$', OccupancyView.as_view(), name='occupancy'),
    url(r'^stats/$', StatsView.as_view(), name='stats'),
]

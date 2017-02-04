from django.conf.urls import url, include
from .views import HomeView, BookingListView, BookingDetailView, CreateAgreementView, OccupancyView


urlpatterns = [
    url(r'^$', HomeView.as_view(), name='home'),
    url(r'^booking/$', BookingListView.as_view(), name='booking_list'),
    url(r'^booking/(?P<pk>\d+)/$', BookingDetailView.as_view(), name='booking_detail'),
    url(r'^booking/(?P<pk>\d+)/create_agreement/$', CreateAgreementView.as_view(), name='create_agreement'),
    url(r'^occupancy/$', OccupancyView.as_view()),
]

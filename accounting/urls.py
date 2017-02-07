from django.conf.urls import url
from .views import BalanceView

urlpatterns = [
    url(r'^balance/', BalanceView.as_view(), name='balance'),
]

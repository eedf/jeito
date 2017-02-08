from django.conf.urls import url
from .views import BalanceView, AnalyticBalanceView, BankStatementView

urlpatterns = [
    url(r'^balance/', BalanceView.as_view(), name='balance'),
    url(r'^analytic-balance/', AnalyticBalanceView.as_view(), name='analytic-balance'),
    url(r'^bank-statement/', BankStatementView.as_view(), name='bank-statement'),
]

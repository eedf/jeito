from django.conf.urls import url
from .views import BalanceView, AnalyticBalanceView, BankStatementView, AccountView, ReconciliationView

urlpatterns = [
    url(r'^balance/', BalanceView.as_view(), name='balance'),
    url(r'^account/', AccountView.as_view(), name='account'),
    url(r'^analytic-balance/', AnalyticBalanceView.as_view(), name='analytic-balance'),
    url(r'^bank-statement/', BankStatementView.as_view(), name='bank-statement'),
    url(r'^reconciliation/(?P<pk>\d+)/', ReconciliationView.as_view(), name='reconciliation'),
]

from django.conf.urls import url
from .views import (BalanceView, AnalyticBalanceView, BankStatementView, AccountView, ReconciliationView,
                    NextReconciliationView, BudgetView, EntryView, EntryListView)


urlpatterns = [
    url(r'^entry/$', EntryListView.as_view(), name='entry_list'),
    url(r'^entry/(?P<pk>\d+)/$', EntryView.as_view(), name='entry'),
    url(r'^budget/$', BudgetView.as_view(), name='budget'),
    url(r'^balance/$', BalanceView.as_view(), name='balance'),
    url(r'^account/$', AccountView.as_view(), name='account'),
    url(r'^analytic-balance/$', AnalyticBalanceView.as_view(), name='analytic-balance'),
    url(r'^bank-statement/$', BankStatementView.as_view(), name='bank-statement'),
    url(r'^reconciliation/next/$', NextReconciliationView.as_view(), name='next_reconciliation'),
    url(r'^reconciliation/(?P<pk>\d+)/$', ReconciliationView.as_view(), name='reconciliation'),
]

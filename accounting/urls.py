from django.conf.urls import url
from .views import (BalanceView, AnalyticBalanceView, BankStatementView, AccountView, ReconciliationView,
                    NextReconciliationView, BudgetView, ProjectionView, EntryView, EntryListView,
                    CashFlowView, CashFlowJsonView)

app_name = 'accounting'

urlpatterns = [
    url(r'^entry/$', EntryListView.as_view(), name='entry_list'),
    url(r'^entry/(?P<pk>\d+)/$', EntryView.as_view(), name='entry'),
    url(r'^budget/$', BudgetView.as_view(), name='budget'),
    url(r'^projection/$', ProjectionView.as_view(), name='projection'),
    url(r'^balance/$', BalanceView.as_view(), name='balance'),
    url(r'^account/$', AccountView.as_view(), name='account'),
    url(r'^analytic-balance/$', AnalyticBalanceView.as_view(), name='analytic-balance'),
    url(r'^bank-statement/$', BankStatementView.as_view(), name='bank-statement'),
    url(r'^reconciliation/next/$', NextReconciliationView.as_view(), name='next_reconciliation'),
    url(r'^reconciliation/(?P<pk>\d+)/$', ReconciliationView.as_view(), name='reconciliation'),
    url(r'^cash-flow/$', CashFlowView.as_view(), name='cash-flow'),
    url(r'^cash-flow/data/$', CashFlowJsonView.as_view(), name='cash_flow_data'),
]

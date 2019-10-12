from django.conf.urls import url
from .views import (BalanceView, ThirdPartyBalanceView, AnalyticBalanceView,
                    BankStatementView, AccountView, ReconciliationView, ThirdPartyCsvView,
                    NextReconciliationView, ProjectionView, EntryView, EntryListView,
                    CashFlowView, CashFlowJsonView, TransferOrderDownloadView, EntryCsvView,
                    ChecksView, PurchaseCreateView, PurchaseUpdateView)


app_name = 'accounting'

urlpatterns = [
    url(r'^(?P<year_pk>\d+)/entry/$', EntryListView.as_view(), name='entry_list'),
    url(r'^(?P<year_pk>\d+)/entry/(?P<pk>\d+)/$', EntryView.as_view(), name='entry'),
    url(r'^(?P<year_pk>\d+)/entry.csv$', EntryCsvView.as_view(), name='entry-csv'),
    url(r'^(?P<year_pk>\d+)/projection/$', ProjectionView.as_view(), name='projection'),
    url(r'^(?P<year_pk>\d+)/balance/$', BalanceView.as_view(), name='balance'),
    url(r'^(?P<year_pk>\d+)/account/$', AccountView.as_view(), name='account'),
    url(r'^(?P<year_pk>\d+)/thirdparty-balance/$', ThirdPartyBalanceView.as_view(), name='thirdparty-balance'),
    url(r'^(?P<year_pk>\d+)/thirdparty.csv$', ThirdPartyCsvView.as_view(), name='thirdparty-csv'),
    url(r'^(?P<year_pk>\d+)/analytic-balance/$', AnalyticBalanceView.as_view(), name='analytic-balance'),
    url(r'^(?P<year_pk>\d+)/bank-statement/$', BankStatementView.as_view(), name='bank-statement'),
    url(r'^(?P<year_pk>\d+)/reconciliation/next/$', NextReconciliationView.as_view(), name='next_reconciliation'),
    url(r'^(?P<year_pk>\d+)/reconciliation/(?P<pk>\d+)/$', ReconciliationView.as_view(), name='reconciliation'),
    url(r'^(?P<year_pk>\d+)/cash-flow/$', CashFlowView.as_view(), name='cash-flow'),
    url(r'^(?P<year_pk>\d+)/cash-flow/data/$', CashFlowJsonView.as_view(), name='cash_flow_data'),
    url(r'^(?P<year_pk>\d+)/transfer-order/(?P<pk>\d+)/download/$', TransferOrderDownloadView.as_view(), name='transfer_order_download'),
    url(r'^(?P<year_pk>\d+)/checks/$', ChecksView.as_view(), name='checks'),
    url(r'^(?P<year_pk>\d+)/purchase/create/$', PurchaseCreateView.as_view(), name='purchase_create'),
    url(r'^(?P<year_pk>\d+)/purchase/(?P<pk>\d+)/update/$', PurchaseUpdateView.as_view(), name='purchase_update'),
]

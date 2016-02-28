from django.conf.urls import url
from . import views


app_name = 'members'

urlpatterns = [
    url(r'^adhesions/$', views.AdhesionsView.as_view(), name='adhesions'),
    url(r'^adhesions/data/$', views.AdhesionsJsonView.as_view(), name='adhesions_data'),
    url(r'^tranches/$', views.TranchesView.as_view(), name='tranches'),
    url(r'^tranches/data/$', views.TranchesJsonView.as_view(), name='tranches_data'),
    url(r'^tableau/regions/$', views.TableauRegionsView.as_view(), name='tableau_regions'),
    url(r'^tableau/functions/$', views.TableauFunctionsView.as_view(), name='tableau_functions'),
]

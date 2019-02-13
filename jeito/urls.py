from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views


urlpatterns = [
    url(r'^login/$', auth_views.LoginView.as_view(), name='login'),
    url(r'^logout/$', auth_views.logout_then_login, name='logout'),
    url(r'^admin/', admin.site.urls),
    url(r'^', include('dashboard.urls')),
    url(r'^members/', include('members.urls')),
    url(r'^booking/', include('booking.urls')),
    url(r'^accounting/', include('accounting.urls')),
    url(r'^tracking/', include('tracking.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if 'docs' in settings.INSTALLED_APPS:
    urlpatterns += [
        url(r'^docs/', include('docs.urls')),
    ]

if settings.DEBUG:
    import debug_toolbar
    urlpatterns += [
        url(r'^__debug__/', include(debug_toolbar.urls)),
    ]

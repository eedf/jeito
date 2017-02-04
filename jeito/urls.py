from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin


urlpatterns = [
    url(r'^admin/', admin.site.urls),
    url(r'^', include('core.urls')),
    url(r'^docs/', include('docs.urls', namespace='docs')),
    url(r'^members/', include('members.urls', namespace='members')),
    url(r'^becours/', include('booking.urls', namespace='booking')),
    url(r'^tracking/', include('tracking.urls')),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

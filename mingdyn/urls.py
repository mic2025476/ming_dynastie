from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.i18n import JavaScriptCatalog
urlpatterns = [
    path('i18n/', include('django.conf.urls.i18n')),
    path('admin/', admin.site.urls),
    path("", include(("mingsite.urls", "mingsite"), namespace="mingsite")),
    path('locations/', include(('locations.urls', 'locations'), namespace='locations')),
    path('menus/', include('menus.urls')),
    path('gallery/', include('gallery.urls')),
    path('reservations/', include('reservations.urls')),
    path('testimonials/', include('testimonials.urls')),
    path('ming/legal/', include('legal.urls')),
    path("", include("qrflow.urls")),
    path("dashboard/", include(("dashboard.urls", "dashboard"), namespace="dashboard")),
    path("jsi18n/", JavaScriptCatalog.as_view(), name="javascript-catalog"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
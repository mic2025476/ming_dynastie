from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('mingsite.urls')),          # homepage, base
    path('locations/', include('locations.urls')),
    path('menus/', include('menus.urls')),
    path('gallery/', include('gallery.urls')),
    path('reservations/', include('reservations.urls')),
    path('testimonials/', include('testimonials.urls')),
    path('ming/legal/', include('legal.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

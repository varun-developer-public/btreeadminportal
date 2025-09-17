from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import home

urlpatterns = [
    path('', home, name='home'),
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')), 
    path('students/', include('studentsdb.urls')),
    path('placements/', include('placementdb.urls')),
    path('batches/', include('batchdb.urls')),
    path('trainers/', include('trainersdb.urls')),
    path('consultants/', include('consultantdb.urls')),
    path('settings/', include('settingsdb.urls')),
    path('payments/', include('paymentdb.urls')),
    path('coursedb/', include('coursedb.urls')),
    path('placement-drive/', include('placementdrive.urls')),
    path('api/', include('coursedb.api_urls')),
    path('api/', include('batchdb.api_urls')),
]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

handler404 = 'core.views.custom_404'
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('accounts.urls')), 
    path('students/', include('studentsdb.urls')),
    path('placements/', include('placementdb.urls')),
    path('batches/', include('batchdb.urls')),
    path('trainers/', include('trainersdb.urls')),
    path('consultants/', include('consultantdb.urls')),
    path('settings/', include('settingsdb.urls')),
]

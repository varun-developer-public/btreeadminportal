from django.urls import path
from . import views

app_name = 'placementdrive'

urlpatterns = [
    path('', views.placement_drive_list, name='drive_list'),
    path('add/', views.placement_drive_create, name='drive_add'),
    path('<int:pk>/edit/', views.placement_drive_update, name='drive_edit'),
    path('<int:pk>/delete/', views.placement_drive_delete, name='drive_delete'),
]
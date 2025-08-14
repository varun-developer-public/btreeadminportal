from django.urls import path
from . import views

app_name = 'placementdrive'

urlpatterns = [
    path('', views.company_list, name='company_list'),
    path('add/', views.company_create, name='company_add'),
    path('<int:pk>/edit/', views.company_update, name='company_edit'),
    path('<int:pk>/delete/', views.company_delete, name='company_delete'),
]
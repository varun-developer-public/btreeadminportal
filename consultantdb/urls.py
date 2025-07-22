from django.urls import path
from . import views
from django.contrib.auth import views as auth_views
from .views import ConsultantProfileUpdateView
from django.urls import reverse_lazy

urlpatterns = [
    path('', views.consultant_list, name='consultant_list'),
    path('create/', views.create_consultant, name='create_consultant'),
    path('update/<int:pk>/', views.update_consultant, name='update_consultant'),
    path('delete/<int:pk>/', views.delete_consultant, name='delete_consultant'),
    path('delete-all/', views.delete_all_consultants, name='delete_all_consultants'),
    path('profile/', ConsultantProfileUpdateView.as_view(), name='consultant_profile'),
]

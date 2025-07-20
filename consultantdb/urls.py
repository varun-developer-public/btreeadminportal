from django.urls import path
from . import views

urlpatterns = [
    path('', views.consultant_list, name='consultant_list'),
    path('create/', views.create_consultant, name='create_consultant'),
    path('update/<int:pk>/', views.update_consultant, name='update_consultant'),
    path('delete/<int:pk>/', views.delete_consultant, name='delete_consultant'),
    path('delete-all/', views.delete_all_consultants, name='delete_all_consultants'),
]

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
    path('password_change/', auth_views.PasswordChangeView.as_view(template_name='consultantdb/password_change_form.html', success_url=reverse_lazy('password_change_done')), name='password_change'),
    path('password_change/done/', auth_views.PasswordChangeDoneView.as_view(template_name='consultantdb/password_change_done.html'), name='password_change_done'),
]

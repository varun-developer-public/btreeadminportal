from django.urls import path
from .views import user_list, create_user, update_user, delete_user, admin_dashboard, staff_dashboard, logout_view, login_view

urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('admin_dashboard/', admin_dashboard, name='admin_dashboard'),
    path('staff_dashboard/', staff_dashboard, name='staff_dashboard'),
    path('users/', user_list, name='user_list'),
    path('users/create/', create_user, name='create_user'),
    path('users/<int:pk>/update/', update_user, name='update_user'),
    path('users/<int:pk>/delete/', delete_user, name='delete_user'),
]

from django.urls import path
from .views import login_view, logout_view, admin_dashboard, staff_dashboard

urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('admin/dashboard/', admin_dashboard, name='admin_dashboard'),
    path('staff/dashboard/', staff_dashboard, name='staff_dashboard'),
]

from django.urls import path
from .views import *

urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('admin_dashboard/', admin_dashboard, name='admin_dashboard'),
    path('staff_dashboard/', staff_dashboard, name='staff_dashboard'),
    path('consultant_dashboard/', consultant_dashboard, name='consultant_dashboard'),
    path('placement_dashboard/', placement_dashboard, name='placement_dashboard'),
    path('trainer_dashboard/', trainer_dashboard, name='trainer_dashboard'),
    path('batch_coordination_dashboard/', batch_coordination_dashboard, name='batch_coordination_dashboard'),
    path('users/', user_list, name='user_list'),
    path('users/create/', create_user, name='create_user'),
    path('users/<int:pk>/update/', update_user, name='update_user'),
    path('users/<int:pk>/delete/', delete_user, name='delete_user'),
    path('password_change/', password_change, name='password_change'),
    path('password_reset/', password_reset_request, name='password_reset_request'),
    path('password_reset/otp/', password_reset_otp, name='password_reset_otp'),
    path('password_reset/new_password/', password_reset_new_password, name='password_reset_new_password'),
    path('verify-2fa/', verify_2fa, name='verify_2fa'),
    path('trainers/availability/', trainers_availabity, name='trainers_availability'),
    path('api/trainer_availability/', trainer_availability_api, name='trainer_availability_api'),
    path('api/trainers_by_course/', trainers_by_course, name='trainers_by_course'),
]

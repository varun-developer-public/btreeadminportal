from django.urls import path
from . import views

urlpatterns = [
    path('', views.settings_dashboard, name='settings_dashboard'),
    path('sources/', views.source_list, name='source_list'),
    path('accounts/', views.payment_account_list, name='payment_account_list'),
    path('logs/', views.transaction_log, name='transaction_log'),
]

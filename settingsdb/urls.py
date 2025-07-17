from django.urls import path
from . import views

urlpatterns = [
    path('', views.settings_dashboard, name='settings_dashboard'),
    path('sources/', views.source_list, name='source_list'),
    path('accounts/', views.payment_account_list, name='payment_account_list'),
    path('sources/remove/<int:pk>/', views.remove_source, name='remove_source'),
    path('accounts/remove/<int:pk>/', views.remove_payment_account, name='remove_payment_account'),
    path('logs/', views.transaction_log, name='transaction_log'),
]

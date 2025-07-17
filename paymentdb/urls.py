from django.urls import path
from . import views

urlpatterns = [
    path('', views.payment_list, name='payment_list'),
    path('<str:payment_id>/update/', views.payment_update, name='payment_update'),
    path('<str:payment_id>/update_emi_date/', views.update_emi_date, name='update_emi_date'),
]

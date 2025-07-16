from django.urls import path
from . import views

urlpatterns = [
    path('', views.payment_list, name='payment_list'),
    path('payments/<int:payment_id>/update/', views.payment_update, name='payment_update'),
]

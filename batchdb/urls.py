from django.urls import path
from .views import batch_list, create_batch, update_batch, delete_batch

urlpatterns = [
    path('', batch_list, name='batch_list'),
    path('create/', create_batch, name='create_batch'),
    path('<int:pk>/update/', update_batch, name='update_batch'),
    path('<int:pk>/delete/', delete_batch, name='delete_batch'),
]

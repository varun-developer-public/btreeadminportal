from django.urls import path
from .views import trainer_list, create_trainer, update_trainer, delete_trainer

urlpatterns = [
    path('', trainer_list, name='trainer_list'),
    path('create/', create_trainer, name='create_trainer'),
    path('update/<int:pk>/', update_trainer, name='update_trainer'),
    path('delete/<int:pk>/', delete_trainer, name='delete_trainer'),
]

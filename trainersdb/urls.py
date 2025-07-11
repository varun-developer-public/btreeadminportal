from django.urls import path
from .views import trainer_list, create_trainer

urlpatterns = [
    path('', trainer_list, name='trainer_list'),
    path('create/', create_trainer, name='create_trainer'),
]

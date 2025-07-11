from django.urls import path
from .views import placement_list, update_placement

urlpatterns = [
    path('', placement_list, name='placement_list'),
    path('<int:pk>/update/', update_placement, name='update_placement'),
]

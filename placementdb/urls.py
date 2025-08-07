from django.urls import path
from .views import placement_list, update_placement, pending_resumes_list

urlpatterns = [
    path('', placement_list, name='placement_list'),
    path('<int:pk>/update/', update_placement, name='update_placement'),
    path('pending-resumes/', pending_resumes_list, name='pending_resumes_list'),
]

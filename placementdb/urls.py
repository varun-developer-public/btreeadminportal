from django.urls import path
from .views import placement_list, update_placement, pending_resumes_list, update_interview, delete_placement

app_name = 'placementdb'

urlpatterns = [
    path('', placement_list, name='placement_list'),
    path('<int:pk>/update/', update_placement, name='update_placement'),
    path('interview/<int:pk>/update/', update_interview, name='update_interview'),
    path('pending-resumes/', pending_resumes_list, name='pending_resumes_list'),
    path('<int:pk>/delete/', delete_placement, name='delete_placement'),
]

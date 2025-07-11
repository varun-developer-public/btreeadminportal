from django.urls import path
from .views import create_student, student_list, update_student,delete_student

urlpatterns = [
    path('', student_list, name='student_list'),
    path('create/', create_student, name='create_student'),
    path('<str:student_id>/update/', update_student, name='update_student'),
    path('<str:student_id>/delete/', delete_student, name='delete_student'),
]

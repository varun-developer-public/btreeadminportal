from django.urls import path
from .views import (
    create_student,
    student_list,
    update_student,
    delete_student,
    download_student_template,
    import_students,
    download_error_report,
    delete_all_students,
    student_report,
)

urlpatterns = [
    path('', student_list, name='student_list'),
    path('create/', create_student, name='create_student'),
    path('<str:student_id>/update/', update_student, name='update_student'),
    path('<str:student_id>/delete/', delete_student, name='delete_student'),
    path('import/', import_students, name='import_students'),
    path('template/', download_student_template, name='download_student_template'),
    path('error-report/', download_error_report, name='download_error_report'),
    path('<str:student_id>/report/', student_report, name='student_report'),
    path('delete-all/', delete_all_students, name='delete_all_students'),
]

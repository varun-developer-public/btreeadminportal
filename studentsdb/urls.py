from django.urls import path
from .views import (
    create_student,
    student_list,
    student_remarks,
    update_student,
    delete_student,
    download_student_template,
    import_students,
    download_error_report,
    delete_all_students,
    student_report, conversation_messages, conversation_send, conversation_upload, get_mentionable_users
)

urlpatterns = [
    path('', student_list, name='student_list'),
    path('remarks/', student_remarks, name='student_remarks'),
    path('create/', create_student, name='create_student'),
    path('<str:student_id>/update/', update_student, name='update_student'),
    path('<str:student_id>/delete/', delete_student, name='delete_student'),
    path('import/', import_students, name='import_students'),
    path('template/', download_student_template, name='download_student_template'),
    path('error-report/', download_error_report, name='download_error_report'),
    path('<str:student_id>/report/', student_report, name='student_report'),
    path('delete-all/', delete_all_students, name='delete_all_students'),
    path('conversation/<int:student_pk>/messages/', conversation_messages, name='conversation_messages'),
    path('conversation/<int:student_pk>/send/', conversation_send, name='conversation_send'),
    path('conversation/<int:student_pk>/upload/', conversation_upload, name='conversation_upload'),
    path('mentionable-users/', get_mentionable_users, name='get_mentionable_users'),
]

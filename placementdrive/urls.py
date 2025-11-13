from django.urls import path
from . import views

urlpatterns = [
    path('', views.company_list, name='company_list'),
    path('create/', views.company_create, name='company_create'),
    path('<int:pk>/update/', views.company_update, name='company_update'),
    path('<int:pk>/delete/', views.company_delete, name='company_delete'),
    path('interviews/', views.interview_list, name='interview_list'),
    path('interview/<int:parent_interview_pk>/add_round/', views.add_interview_round, name='add_interview_round'),
    path('interview/<int:interview_pk>/update_students/', views.update_interview_students, name='update_interview_students'),
    path('interview-student/<int:student_interview_pk>/remove/', views.remove_interview_student, name='remove_interview_student'),
    path('ajax/load-students/', views.load_students, name='ajax_load_students'),
    path('interview/<int:interview_pk>/postpone/', views.postpone_interview_round, name='postpone_interview_round'),
    path('interview/<int:interview_pk>/delete/', views.delete_interview_round, name='delete_interview_round'),
    path('company/<int:pk>/restart/', views.restart_interview_cycle, name='restart_interview_cycle'),
    path('resume-status/<int:status_pk>/edit/', views.edit_resume_shared_status, name='edit_resume_shared_status'),
]

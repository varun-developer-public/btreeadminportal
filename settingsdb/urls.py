from django.urls import path
from . import views

urlpatterns = [
    path('', views.settings_dashboard, name='settings_dashboard'),
    path('sources/', views.source_list, name='source_list'),
    path('accounts/', views.payment_account_list, name='payment_account_list'),
    path('sources/remove/<int:pk>/', views.remove_source, name='remove_source'),
    path('accounts/remove/<int:pk>/', views.remove_payment_account, name='remove_payment_account'),
    path('logs/', views.transaction_log, name='transaction_log'),
    path('export/', views.export_data, name='export_data'),
    path('import/', views.import_data, name='import_data'),
    path('delete-all-courses/', views.delete_all_courses, name='delete_all_courses'),
    path('delete-all-course-categories/', views.delete_all_course_categories, name='delete_all_course_categories'),
    path('import-courses/', views.import_student_courses, name='import_student_courses'),
    path('download-course-template/', views.download_course_template, name='download_course_template'),
    path('export-student-courses/', views.export_student_courses, name='export_student_courses'),
]

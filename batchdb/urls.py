from django.urls import path, include
from . import views

app_name = 'batchdb'

urlpatterns = [
    # Include API router URLs
    path('api/', include('batchdb.api_urls')),
    
    # Traditional views
    path('requests/', views.RequestListView.as_view(), name='requests_list'),
    path('list/', views.batch_list, name='batch_list'),
    path('create/', views.create_batch, name='create_batch'),
    path('<int:pk>/update/', views.update_batch, name='update_batch'),
    path('import/', views.import_batches, name='import_batches'),
    path('template/', views.download_batch_template, name='download_batch_template'),
    path('error-report/', views.download_error_report_batch, name='download_error_report_batch'),
    path('<int:pk>/delete/', views.delete_batch, name='delete_batch'),
    path('batch/<int:pk>/report/', views.batch_report, name='batch_report'),
    path('batch/<int:batch_id>/export/', views.export_batch_data, name='export_batch_data'),
    path('export-all/', views.export_all_batches_data, name='export_all_batches_data'),
    path('handover-requests/', views.view_handover_requests, name='view_handover_requests'),
    path('handover-requests/<int:pk>/update/', views.update_handover_status, name='update_handover_status'),
    
    # Student history report
    path('student/history/', views.student_batch_history, name='student-batch-history'),

    # AJAX URLs
    path('ajax/get-courses-by-category/', views.get_courses_by_category, name='get_courses_by_category'),
    path('ajax/get-trainers-for-course/', views.get_trainers_for_course, name='get_trainers_for_course'),
    path('ajax/get-trainer-slots/', views.get_trainer_slots, name='get_trainer_slots'),
    path('ajax/get-students-for-course/', views.get_students_for_course, name='get_students_for_course'),
    path('ajax/get-trainers-by-course/', views.get_trainers_by_course, name='get_trainers_by_course'),
    path('ajax/get-students-by-course/', views.get_students_by_course, name='get_students_by_course'),
    path('ajax/get-students-for-batch/', views.get_students_for_batch, name='get_students_for_batch'),
    path('ajax/get-students-not-in-batch/', views.get_students_not_in_batch, name='get_students_not_in_batch'),
    
    # Request management endpoints
    path('requests/<int:request_id>/details/', views.request_details, name='request_details'),
    path('requests/<int:request_id>/approve/', views.approve_request, name='approve_request'),
    path('requests/<int:request_id>/reject/', views.reject_request, name='reject_request'),
]

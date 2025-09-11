from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create a router for API ViewSets
router = DefaultRouter()
router.register(r'api/batches', views.BatchViewSet)
router.register(r'api/transfer-requests', views.TransferRequestViewSet)
router.register(r'api/trainer-handovers', views.TrainerHandoverViewSet)
router.register(r'api/transactions', views.BatchTransactionViewSet)

app_name = 'batchdb'

urlpatterns = [
    # Include API router URLs
    path('', include(router.urls)),
    
    # Traditional views
    path('', views.batch_list, name='batch_list'),
    path('create/', views.create_batch, name='create_batch'),
    path('<int:pk>/update/', views.update_batch, name='update_batch'),
    path('import/', views.import_batches, name='import_batches'),
    path('template/', views.download_batch_template, name='download_batch_template'),
    path('error-report/', views.download_error_report_batch, name='download_error_report_batch'),
    path('<int:pk>/delete/', views.delete_batch, name='delete_batch'),
    
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
]

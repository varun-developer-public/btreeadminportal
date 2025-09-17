from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'batches', views.BatchViewSet, basename='batch')
router.register(r'transfer-requests', views.TransferRequestViewSet, basename='transferrequest')
router.register(r'trainer-handovers', views.TrainerHandoverViewSet, basename='trainerhandover')
router.register(r'transactions', views.BatchTransactionViewSet, basename='batchtransaction')
router.register(r'student-history', views.StudentHistoryViewSet, basename='studenthistory')

app_name = 'batchdb_api'

urlpatterns = [
    path('', include(router.urls)),
    path('available-students-for-transfer/', views.available_students_for_transfer, name='available-students-for-transfer'),
    path('available-batches-for-transfer/', views.available_batches_for_transfer, name='available-batches-for-transfer'),
    path('available-trainers-for-handover/', views.available_trainers_for_handover, name='available-trainers-for-handover'),
    path('available-batches-for-handover/', views.available_batches_for_handover, name='available-batches-for-handover'),
    path('batches/<int:pk>/add_student/', views.BatchViewSet.as_view({'post': 'add_student'}), name='batch-add-student'),
    path('batches/<int:pk>/remove_student/', views.BatchViewSet.as_view({'post': 'remove_student'}), name='batch-remove-student'),
]
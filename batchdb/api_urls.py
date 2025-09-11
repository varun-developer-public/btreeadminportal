from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'batches', views.BatchViewSet, basename='batch')
router.register(r'transfer-requests', views.TransferRequestViewSet, basename='transferrequest')
router.register(r'trainer-handovers', views.TrainerHandoverViewSet, basename='trainerhandover')
router.register(r'transactions', views.BatchTransactionViewSet, basename='batchtransaction')

app_name = 'batchdb_api'

urlpatterns = [
    path('', include(router.urls)),
]
from django.urls import path
from .views import batch_list, create_batch, update_batch, delete_batch, import_batches, download_batch_template, download_error_report_batch

urlpatterns = [
    path('', batch_list, name='batch_list'),
    path('create/', create_batch, name='create_batch'),
    path('<int:pk>/update/', update_batch, name='update_batch'),
    path('<int:pk>/delete/', delete_batch, name='delete_batch'),
    path('import/', import_batches, name='import_batches'),
    path('template/', download_batch_template, name='download_batch_template'),
    path('error-report/', download_error_report_batch, name='download_error_report_batch'),
]

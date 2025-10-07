from django.urls import path, include
from . import views

app_name = 'coursedb'

urlpatterns = [
    # Course URLs
    path('courses/', views.course_list, name='course_list'),
    path('courses/create/', views.course_create, name='course_create'),
    path('courses/<int:pk>/update/', views.course_update, name='course_update'),
    path('courses/<int:pk>/delete/', views.course_delete, name='course_delete'),
    path('ajax/course/<int:pk>/get-duration/', views.get_course_duration, name='get_course_duration'),
    path('ajax/get_next_course_code/', views.get_next_course_code, name='get_next_course_code'),
    path('courses/export/', views.export_courses_csv, name='export_courses_csv'),
    path('courses/import/', views.import_courses_csv, name='import_courses_csv'),
    path('courses/download_sample_csv/', views.download_sample_csv, name='download_sample_csv'),

    # Course Category URLs
    path('categories/', views.category_list, name='category_list'),
    path('categories/create/', views.category_create, name='category_create'),
    path('categories/<int:pk>/update/', views.category_update, name='category_update'),
    path('categories/<int:pk>/delete/', views.category_delete, name='category_delete'),

    # API URLs
    path('api/', include('coursedb.api_urls')),
]
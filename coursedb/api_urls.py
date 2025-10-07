from django.urls import path
from . import api_views

urlpatterns = [
    path('courses-by-category/<int:category_id>/', api_views.courses_by_category, name='api_courses_by_category'),
    path('course-list/', api_views.course_list_api, name='course_list_api'),
]
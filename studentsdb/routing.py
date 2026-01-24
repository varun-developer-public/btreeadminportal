from django.urls import re_path
from .consumers import StudentConsumer, StudentRemarksConsumer

websocket_urlpatterns = [
    re_path(r'ws/student/(?P<student_id>\d+)/$', StudentConsumer.as_asgi()),
    re_path(r'ws/student/remarks/$', StudentRemarksConsumer.as_asgi()),
]

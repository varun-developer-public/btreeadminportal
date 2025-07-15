# settingsdb/middleware.py

from .signals import set_current_user
from threading import local

_user = local()

class CaptureUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        try:
            if request.user.is_authenticated:
                set_current_user(request.user)
            else:
                set_current_user(None)
            response = self.get_response(request)
        finally:
            # Clear user after response to avoid leaking user data between requests
            set_current_user(None)
        return response

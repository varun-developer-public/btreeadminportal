# settingsdb/middleware.py
from django.shortcuts import redirect
from django.urls import reverse
from .signals import set_current_user
from threading import local

_user = local()

class CaptureUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            set_current_user(request.user)
            
            # Role-based access control logic
            if request.user.role == 'batch_coordinator':
                restricted_paths = [
                    reverse('coursedb:category_list'),
                    reverse('coursedb:category_create'),
                ]
                # Also handle dynamic URLs like category_update and category_delete
                if request.path in restricted_paths or 'category/update' in request.path or 'category/delete' in request.path:
                    return redirect('accounts:batch_coordination_dashboard')
        else:
            set_current_user(None)
            
        response = self.get_response(request)
        
        # Clear user after response to avoid leaking user data between requests
        set_current_user(None)
        return response

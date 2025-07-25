from django.shortcuts import redirect
from django.http import HttpResponseForbidden
from django.urls import reverse, resolve

# Define role-based access control mappings
URL_ROLE_MAPPINGS = {
    'staff': [
        'staff_dashboard', 'student_list', 'create_student', 'update_student', 'import_students', 'download_student_template', 'download_error_report',
        'batch_list', 'create_batch', 'update_batch', 'import_batches', 'download_batch_template', 'download_error_report_batch',
        'payment_list', 'payment_update', 'update_emi_date',
        'placement_list', 'update_placement',
        'consultant_list', 'create_consultant', 'update_consultant',
        'settings_dashboard', 'source_list', 'payment_account_list', 'remove_source', 'remove_payment_account',
        'user_list', 'create_user', 'update_user',
        'get_courses',
    ],
    'placement': [
        'placement_list', 'update_placement',
        'student_list',
        'batch_list',
    ],
    'trainer': [
        'batch_list',
        'student_list',
    ],
    'batch_coordination': [
        'batch_list', 'create_batch', 'update_batch', 'delete_batch',
        'student_list',
        'trainer_list',
    ],
    'consultant': [
        'consultant_profile',
        'student_list',
        'payment_list', 'payment_update',
        'create_student', 'update_student', 'get_courses','consultant_dashboard'
    ]
}

# URLs accessible to all authenticated users
PUBLIC_URLS = [
    'home', 'logout', 'login',
    'password_change', 'password_change_done'
]

class RolePermissionsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Bypass for media files
            if request.path.startswith('/media/'):
                return self.get_response(request)

            current_url_name = resolve(request.path_info).url_name

            # Bypass for public URLs and admin users
            if current_url_name in PUBLIC_URLS or request.user.role in ['admin', 'staff']:
                return self.get_response(request)

            # Check permissions for other roles
            user_role = request.user.role
            if user_role in URL_ROLE_MAPPINGS:
                if current_url_name not in URL_ROLE_MAPPINGS[user_role]:
                    return HttpResponseForbidden("You do not have permission to access this page.")
            else:
                # If role is not in mappings, deny access by default
                return HttpResponseForbidden("Your role does not have permissions defined.")

        return self.get_response(request)


class RoleBasedRedirectMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if request.user.is_authenticated:
            if request.user.role == 'consultant' and request.path == reverse('admin_dashboard'):
                return redirect('consultant_profile')
        return response
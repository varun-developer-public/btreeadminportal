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
        'get_courses', 'company_list','company_create','company_update','schedule_interview','add_interview_round','update_interview_students',
        'ajax_load_students','consultant_dashboard','request_details','approve_request',
        'reject_request','available-students-for-transfer','available-batches-for-transfer',
        'available-trainers-for-handover','available-batches-for-handover','batch-add-student','batch-remove-student',
        'api_courses_by_category','get_course_duration','transfer-requests',
        'batch-list','batch-detail',
        'transferrequest-list','transferrequest-detail',
        'trainerhandover-list','trainerhandover-detail',
        'batchtransaction-list','batchtransaction-detail',
        'studenthistory-list','studenthistory-detail','batch_report','interview_list',
        'course_list_api','trainer_availability_api','trainers_availability','trainers_by_course','requests_list','student_report'
    ],
    'placement': [
        'placement_dashboard',
        'placement_list', 'update_placement', 'pending_resumes_list',
        'student_list', 'update_student',
        'batch_list','drive_list', 'drive_add', 'drive_edit', 'get_courses',
        'company_list','company_create','company_update','schedule_interview','add_interview_round','update_interview_students',
        'ajax_load_students','postpone_interview_round', 'restart_interview_cycle','student_report','api_courses_by_category','edit_resume_shared_status',
        'delete_placement','batch_report','interview_list'
    ],
    'trainer': [
        'trainer_dashboard',
        'batch_list',
        'student_list','batch_report','student_report',
        'batch_list','update_batch','course_list','category_list','course_create','course_update','get_next_course_code','get_courses_by_category'
    ],
    'batch_coordination': [
        'batch_coordination_dashboard',
        'batch_list', 'create_batch', 'update_batch',
        'student_list',
        'trainer_list', 'create_trainer', 'update_trainer',
        'update_user',
        'password_change',
        'course_list',
        'category_list',
        'course_create',
        'course_update',
        'category_create',
        'category_update',
        'get_next_course_code','get_courses_by_category','requests_list',
        'get_students_not_in_batch','get_students_for_batch','get_students_by_course','get_trainers_by_course',
        'get_students_for_course','get_trainer_slots','get_trainers_for_course','get_courses_by_category',
        'export_batch_data','student-batch-history','request_details','approve_request',
        'reject_request','available-students-for-transfer','available-batches-for-transfer',
        'available-trainers-for-handover','available-batches-for-handover','batch-add-student','batch-remove-student',
        'api_courses_by_category','get_course_duration','transfer-requests',
        'batch-list','batch-detail',
        'transferrequest-list','transferrequest-detail',
        'trainerhandover-list','trainerhandover-detail',
        'batchtransaction-list','batchtransaction-detail',
        'studenthistory-list','studenthistory-detail','batch_report',
        'course_list_api','trainer_availability_api','trainers_availability','trainers_by_course','student_report'
    ],
    'consultant': [
        'consultant_profile',
        'student_list',
        'payment_list', 'payment_update',
        'create_student', 'update_student', 'get_courses','consultant_dashboard','course_list',
        'category_list','get_courses_by_category','get_trainers_for_course','get_trainer_slots','get_students_for_course',
        'get_next_course_code','get_course_duration','batch_report','course_list_api','trainer_availability_api','trainers_availability','trainers_by_course','student_report'
    ]
}

# URLs accessible to all authenticated users
PUBLIC_URLS = [
    'home', 'logout', 'login',
    'password_change', 'password_change_done','manage_2fa','verify_2fa'
]

class RolePermissionsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            # Bypass for media files
            if request.path.startswith('/media/') or request.path.startswith('/batches/api/'):
                return self.get_response(request)

            current_url_name = resolve(request.path_info).url_name
            
            print("DEBUG URL NAME:", current_url_name, request.path)

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
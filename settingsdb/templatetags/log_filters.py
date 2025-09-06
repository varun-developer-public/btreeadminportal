from django import template
import json
from django.utils.html import format_html

register = template.Library()

@register.filter
def format_changes(changes):
    try:
        changes_dict = json.loads(changes)
        if not isinstance(changes_dict, dict):
            return changes
        
        formatted_changes = []
        for key, value in changes_dict.items():
            if key == 'csrfmiddlewaretoken':
                continue
            
            old_value, new_value = value
            
            # Handle cases where values might be lists
            if isinstance(old_value, list):
                old_value = ', '.join(map(str, old_value))
            if isinstance(new_value, list):
                new_value = ', '.join(map(str, new_value))

            # Improve readability for specific fields
            key_display = key.replace('_', ' ').title()

            if old_value is None or old_value == '':
                formatted_changes.append(f"Set {key_display} to '{new_value}'")
            else:
                formatted_changes.append(f"Changed {key_display} from '{old_value}' to '{new_value}'")
                
        return "\n".join(formatted_changes)
    except (json.JSONDecodeError, TypeError, ValueError):
        return changes

@register.filter
def format_activity_description(log):
    """Provides a more detailed and user-friendly description of the activity."""
    try:
        # Get basic information
        action = log.action
        table_name = log.table_name
        changes_dict = log.changes if isinstance(log.changes, dict) else {}
        
        # Get app name for context
        app_name = changes_dict.get('app', '')
        
        # Initialize description parts
        description = ""
        
        # Handle different models with specific formatting
        if table_name == 'Student':
            student_id = changes_dict.get('student_id', 'N/A')
            full_name = f"{changes_dict.get('first_name', '')} {changes_dict.get('last_name', '')}".strip()
            if action == 'CREATE':
                description = f"Enrolled new student <strong>{full_name}</strong> with ID <strong>{student_id}</strong>"
            elif action == 'UPDATE':
                description = f"Updated profile for student <strong>{full_name}</strong> (ID: <strong>{student_id}</strong>)"
            elif action == 'DELETE':
                description = f"Removed student <strong>{full_name}</strong> (ID: <strong>{student_id}</strong>)"

        elif table_name == 'Payment':
            payment_id = changes_dict.get('payment_id', 'N/A')
            student_name = changes_dict.get('student', 'N/A')
            if action == 'CREATE':
                description = f"Created new payment record <strong>{payment_id}</strong> for student <strong>{student_name}</strong>"
            elif action == 'UPDATE':
                description = f"Updated payment details for <strong>{payment_id}</strong> (Student: <strong>{student_name}</strong>)"
            elif action == 'DELETE':
                description = f"Deleted payment record <strong>{payment_id}</strong> for student <strong>{student_name}</strong>"

        elif table_name == 'Batch':
            batch_id = changes_dict.get('batch_id', 'N/A')
            course_name = changes_dict.get('course', 'N/A')
            if action == 'CREATE':
                description = f"Created new batch <strong>{batch_id}</strong> for course <strong>{course_name}</strong>"
            elif action == 'UPDATE':
                description = f"Updated batch <strong>{batch_id}</strong>"
            elif action == 'DELETE':
                description = f"Deleted batch <strong>{batch_id}</strong>"

        elif table_name == 'Placement':
            student_name = changes_dict.get('student', 'N/A')
            if action == 'CREATE':
                description = f"Initiated placement process for <strong>{student_name}</strong>"
            elif action == 'UPDATE':
                description = f"Updated placement status for <strong>{student_name}</strong>"
            elif action == 'DELETE':
                description = f"Removed placement record for <strong>{student_name}</strong>"

        elif table_name == 'Course':
            course_name = changes_dict.get('course_name', 'N/A')
            course_code = changes_dict.get('code', 'N/A')
            if action == 'CREATE':
                description = f"Added new course <strong>{course_name}</strong> with code <strong>{course_code}</strong>"
            elif action == 'UPDATE':
                description = f"Updated course details for <strong>{course_name}</strong> (Code: <strong>{course_code}</strong>)"
            elif action == 'DELETE':
                description = f"Deleted course <strong>{course_name}</strong> (Code: <strong>{course_code}</strong>)"

        elif table_name == 'CourseCategory':
            category_name = changes_dict.get('name', 'N/A')
            category_code = changes_dict.get('code', 'N/A')
            if action == 'CREATE':
                description = f"Created new course category <strong>{category_name}</strong> with code <strong>{category_code}</strong>"
            elif action == 'UPDATE':
                description = f"Updated course category <strong>{category_name}</strong>"
            elif action == 'DELETE':
                description = f"Deleted course category <strong>{category_name}</strong>"

        elif table_name == 'Consultant':
            consultant_name = changes_dict.get('name', 'N/A')
            consultant_id = changes_dict.get('consultant_id', 'N/A')
            if action == 'CREATE':
                description = f"Onboarded new consultant <strong>{consultant_name}</strong> with ID <strong>{consultant_id}</strong>"
            elif action == 'UPDATE':
                description = f"Updated profile for consultant <strong>{consultant_name}</strong> (ID: <strong>{consultant_id}</strong>)"
            elif action == 'DELETE':
                description = f"Removed consultant <strong>{consultant_name}</strong> (ID: <strong>{consultant_id}</strong>)"

        elif table_name == 'Company':
            company_name = changes_dict.get('company_name', 'N/A')
            company_code = changes_dict.get('company_code', 'N/A')
            if action == 'CREATE':
                description = f"Registered new company <strong>{company_name}</strong> with code <strong>{company_code}</strong>"
            elif action == 'UPDATE':
                description = f"Updated profile for company <strong>{company_name}</strong> (Code: <strong>{company_code}</strong>)"
            elif action == 'DELETE':
                description = f"Deleted company <strong>{company_name}</strong> (Code: <strong>{company_code}</strong>)"

        elif table_name == 'Trainer':
            trainer_name = changes_dict.get('name', 'N/A')
            trainer_id = changes_dict.get('trainer_id', 'N/A')
            if action == 'CREATE':
                description = f"Onboarded new trainer <strong>{trainer_name}</strong> with ID <strong>{trainer_id}</strong>"
            elif action == 'UPDATE':
                description = f"Updated profile for trainer <strong>{trainer_name}</strong> (ID: <strong>{trainer_id}</strong>)"
            elif action == 'DELETE':
                description = f"Removed trainer <strong>{trainer_name}</strong> (ID: <strong>{trainer_id}</strong>)"

        elif table_name == 'CustomUser':
            user_name = changes_dict.get('name', 'N/A')
            user_role = changes_dict.get('role', 'N/A')
            if action == 'CREATE':
                description = f"Created new user <strong>{user_name}</strong> with role <strong>{user_role}</strong>"
            elif action == 'UPDATE':
                description = f"Updated profile for user <strong>{user_name}</strong>"
            elif action == 'DELETE':
                description = f"Deleted user <strong>{user_name}</strong>"

        elif table_name == 'CourseModule':
            module_name = changes_dict.get('name', 'N/A')
            course_name = changes_dict.get('course', 'N/A')
            if action == 'CREATE':
                description = f"Added new module <strong>{module_name}</strong> to course <strong>{course_name}</strong>"
            elif action == 'UPDATE':
                description = f"Updated module <strong>{module_name}</strong> in course <strong>{course_name}</strong>"
            elif action == 'DELETE':
                description = f"Deleted module <strong>{module_name}</strong> from course <strong>{course_name}</strong>"

        elif table_name == 'Topic':
            topic_name = changes_dict.get('name', 'N/A')
            module_name = changes_dict.get('module', 'N/A')
            if action == 'CREATE':
                description = f"Added new topic <strong>{topic_name}</strong> to module <strong>{module_name}</strong>"
            elif action == 'UPDATE':
                description = f"Updated topic <strong>{topic_name}</strong> in module <strong>{module_name}</strong>"
            elif action == 'DELETE':
                description = f"Deleted topic <strong>{topic_name}</strong> from module <strong>{module_name}</strong>"

        elif table_name == 'ConsultantProfile':
            user_name = changes_dict.get('user', 'N/A')
            consultant_name = changes_dict.get('consultant', 'N/A')
            if action == 'CREATE':
                description = f"Linked user <strong>{user_name}</strong> to consultant profile <strong>{consultant_name}</strong>"
            elif action == 'UPDATE':
                description = f"Updated consultant profile for <strong>{consultant_name}</strong>"
            elif action == 'DELETE':
                description = f"Unlinked user from consultant profile <strong>{consultant_name}</strong>"

        elif table_name == 'Goal':
            goal_title = changes_dict.get('title', 'N/A')
            consultant_name = changes_dict.get('consultant', 'N/A')
            if action == 'CREATE':
                description = f"Set new goal '<strong>{goal_title}</strong>' for consultant <strong>{consultant_name}</strong>"
            elif action == 'UPDATE':
                description = f"Updated goal '<strong>{goal_title}</strong>' for consultant <strong>{consultant_name}</strong>"
            elif action == 'DELETE':
                description = f"Deleted goal '<strong>{goal_title}</strong>' for consultant <strong>{consultant_name}</strong>"

        elif table_name == 'Achievement':
            achievement_title = changes_dict.get('title', 'N/A')
            consultant_name = changes_dict.get('consultant', 'N/A')
            if action == 'CREATE':
                description = f"Recorded new achievement '<strong>{achievement_title}</strong>' for consultant <strong>{consultant_name}</strong>"
            elif action == 'UPDATE':
                description = f"Updated achievement '<strong>{achievement_title}</strong>' for consultant <strong>{consultant_name}</strong>"
            elif action == 'DELETE':
                description = f"Deleted achievement '<strong>{achievement_title}</strong>' for consultant <strong>{consultant_name}</strong>"

        elif table_name == 'CompanyInterview':
            company_name = changes_dict.get('company', 'N/A')
            student_name = changes_dict.get('student', 'N/A')
            interview_round = changes_dict.get('interview_round', 'N/A')
            if action == 'CREATE':
                description = f"Scheduled <strong>{interview_round}</strong> interview for <strong>{student_name}</strong> with <strong>{company_name}</strong>"
            elif action == 'UPDATE':
                description = f"Updated <strong>{interview_round}</strong> interview details for <strong>{student_name}</strong> with <strong>{company_name}</strong>"
            elif action == 'DELETE':
                description = f"Canceled <strong>{interview_round}</strong> interview for <strong>{student_name}</strong> with <strong>{company_name}</strong>"

        elif table_name == 'ResumeSharedStatus':
            company_name = changes_dict.get('company', 'N/A')
            status = changes_dict.get('status', 'N/A')
            if action == 'CREATE':
                description = f"Shared resume with <strong>{company_name}</strong>"
            elif action == 'UPDATE':
                description = f"Updated resume status to <strong>{status}</strong> for company <strong>{company_name}</strong>"
            elif action == 'DELETE':
                description = f"Deleted resume sharing status for <strong>{company_name}</strong>"

        elif table_name == 'Interview':
            company_name = changes_dict.get('company', 'N/A')
            applying_role = changes_dict.get('applying_role', 'N/A')
            interview_round = changes_dict.get('interview_round', 'N/A')
            if action == 'CREATE':
                description = f"Scheduled <strong>{interview_round}</strong> interview for <strong>{applying_role}</strong> at <strong>{company_name}</strong>"
            elif action == 'UPDATE':
                description = f"Updated <strong>{interview_round}</strong> interview details for <strong>{applying_role}</strong> at <strong>{company_name}</strong>"
            elif action == 'DELETE':
                description = f"Canceled <strong>{interview_round}</strong> interview for <strong>{applying_role}</strong> at <strong>{company_name}</strong>"

        elif table_name == 'InterviewStudent':
            student_name = changes_dict.get('student', 'N/A')
            interview_role = changes_dict.get('interview', 'N/A')
            status = changes_dict.get('status', 'N/A')
            if action == 'CREATE':
                description = f"Added <strong>{student_name}</strong> to the interview for <strong>{interview_role}</strong>"
            elif action == 'UPDATE':
                description = f"Updated interview status for <strong>{student_name}</strong> to <strong>{status}</strong> for the <strong>{interview_role}</strong> role"
            elif action == 'DELETE':
                description = f"Removed <strong>{student_name}</strong> from the interview for <strong>{interview_role}</strong>"

        elif table_name == 'SourceOfJoining':
            source_name = changes_dict.get('name', 'N/A')
            if action == 'CREATE':
                description = f"Added new joining source: <strong>{source_name}</strong>"
            elif action == 'UPDATE':
                description = f"Updated joining source to <strong>{source_name}</strong>"
            elif action == 'DELETE':
                description = f"Deleted joining source: <strong>{source_name}</strong>"

        elif table_name == 'PaymentAccount':
            account_name = changes_dict.get('name', 'N/A')
            if action == 'CREATE':
                description = f"Added new payment account: <strong>{account_name}</strong>"
            elif action == 'UPDATE':
                description = f"Updated payment account: <strong>{account_name}</strong>"
            elif action == 'DELETE':
                description = f"Deleted payment account: <strong>{account_name}</strong>"

        elif table_name == 'UserSettings':
            user_name = changes_dict.get('user', 'N/A')
            enable_2fa = changes_dict.get('enable_2fa', False)
            if action == 'CREATE':
                description = f"Configured initial settings for user <strong>{user_name}</strong>"
            elif action == 'UPDATE':
                status = "enabled" if enable_2fa else "disabled"
                description = f"Updated settings for user <strong>{user_name}</strong> (2FA is now <strong>{status}</strong>)"
            elif action == 'DELETE':
                description = f"Deleted all settings for user <strong>{user_name}</strong>"
        
        # Default fallback if no specific formatting is defined
        if not description:
            if action == 'CREATE':
                description = f"Created new {table_name}"
            elif action == 'UPDATE':
                description = f"Updated {table_name}"
            elif action == 'DELETE':
                description = f"Deleted {table_name}"
            else:
                description = f"{action} {table_name}"
            
        return format_html(description)
    except Exception as e:
        # Fallback to basic description in case of errors
        return f"{log.action} {log.table_name}"

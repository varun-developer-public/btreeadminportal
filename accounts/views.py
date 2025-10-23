from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
import pyotp
from .forms import TwoFactorForm

from consultantdb.models import Achievement, Goal
from .models import CustomUser
from settingsdb.models import UserSettings
from .forms import UserForm, UserUpdateForm, PasswordChangeForm, PasswordResetForm

def is_admin(user):
    return user.is_authenticated and (user.role == 'admin' or user.is_superuser)

def is_staff(user):
    return user.is_authenticated and (user.role == 'staff' or user.is_superuser)

def is_consultant(user):
    return user.is_authenticated and (user.role == 'consultant' or user.is_superuser or user.role == 'staff')

def is_placement(user):
    return user.is_authenticated and (user.role == 'placement' or user.is_superuser)

def is_trainer(user):
    return user.is_authenticated and (user.role == 'trainer' or user.is_superuser)

def is_batch_coordinator(user):
    return user.is_authenticated and (user.role == 'batch_coordination' or user.is_superuser)
from django.db.models import Sum, Q, F
from batchdb.models import Batch
from django.db.models.functions import TruncMonth
from studentsdb.models import Student
from paymentdb.models import Payment
from settingsdb.models import TransactionLog
from placementdb.models import Placement
from placementdrive.models import Company
from datetime import datetime

from django.utils import timezone
from datetime import timedelta
from trainersdb.models import Trainer
from django.db.models import Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    # Basic Statistics
    total_students = Student.objects.count()
    total_pending_amount = Payment.objects.aggregate(total_pending=Sum('total_pending_amount'))['total_pending'] or 0
    active_trainers = Trainer.objects.count()  # Count all trainers since there's no active status

    # Get placement rate using course_status field
    total_completed = Student.objects.filter(course_status='C').count()
    total_placed = Student.objects.filter(course_status='P').count()
    placement_rate = (total_placed / total_completed * 100) if total_completed > 0 else 0

    # Monthly student enrollment
    now = timezone.now()
    six_months_ago = now - timedelta(days=180)
    monthly_enrollments = (
        Student.objects
        .filter(enrollment_date__gte=six_months_ago)
        .annotate(month=TruncMonth('enrollment_date'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )

    enrollment_data = [
        {'month': item['month'].strftime('%Y-%m'), 'count': item['count']}
        for item in monthly_enrollments
    ]

    # Monthly pending amounts for the last 6 months
    monthly_pending_data = {}
    
    # Initialize months to ensure all 6 months are present in the chart
    current_date = now.date()
    for _ in range(6):
        month_key = current_date.strftime('%Y-%m')
        monthly_pending_data[month_key] = 0
        # Go to the first day of the current month, then subtract one day to get the last day of the previous month
        first_day_of_month = current_date.replace(day=1)
        current_date = first_day_of_month - timedelta(days=1)

    pending_payments = Payment.objects.filter(total_pending_amount__gt=0)

    for payment in pending_payments:
        for i in range(1, 5):
            due_date = getattr(payment, f'emi_{i}_date')
            amount = getattr(payment, f'emi_{i}_amount')
            paid_amount = getattr(payment, f'emi_{i}_paid_amount')

            if due_date and amount and not paid_amount and six_months_ago.date() <= due_date <= now.date():
                month_key = due_date.strftime('%Y-%m')
                if month_key in monthly_pending_data:
                    monthly_pending_data[month_key] += float(amount)

    monthly_pending_data = [
        {'month': key, 'amount': value}
        for key, value in sorted(monthly_pending_data.items())
    ]

    # Weekly Statistics
    one_week_ago = now - timedelta(days=7)
    weekly_students = Student.objects.filter(enrollment_date__gte=one_week_ago).count()
    weekly_payments = Payment.objects.filter(student__enrollment_date__gte=one_week_ago).aggregate(
        total=Sum('amount_paid')
    )['total'] or 0

    # Recent Activities and Students
    recent_activities = TransactionLog.objects.order_by('-timestamp')[:10]
    recent_students = Student.objects.order_by('-enrollment_date')[:5]

    # Fetch upcoming payments
    pending_payments = Payment.objects.filter(total_pending_amount__gt=0).select_related('student', 'student__consultant')
    
    # Get all unique course IDs from the students in pending payments
    student_course_ids = [p.student.course_id for p in pending_payments if p.student and p.student.course_id]
    
    # Fetch all relevant courses in a single query
    from coursedb.models import Course
    courses = Course.objects.filter(id__in=student_course_ids)
    course_map = {course.id: course.course_name for course in courses}

    upcoming_payments_list = []
    today = timezone.now().date()

    for payment in pending_payments:
        for i in range(1, 5):
            due_date = getattr(payment, f'emi_{i}_date')
            amount = getattr(payment, f'emi_{i}_amount')
            paid_amount = getattr(payment, f'emi_{i}_paid_amount')

            if due_date and amount and not paid_amount:
                total_paid_by_student = payment.amount_paid or 0
                for j in range(1, 5):
                    total_paid_by_student += getattr(payment, f'emi_{j}_paid_amount') or 0
                
                course_name = course_map.get(payment.student.course_id, 'N/A') if payment.student else 'N/A'

                upcoming_payments_list.append({
                    'student_id': payment.student.student_id,
                    'student_name': f"{payment.student.first_name} {payment.student.last_name or ''}",
                    'mobile': payment.student.phone,
                    'course': course_name,
                    'consultant': payment.student.consultant.name if payment.student.consultant else 'N/A',
                    'emi_number': i,
                    'course_fee': payment.total_fees or 0,
                    'amount': amount,
                    'paid': total_paid_by_student,
                    'due_date': due_date,
                })
                break


    # Sort all upcoming payments by due date and take the first 5.
    upcoming_payments_list.sort(key=lambda x: x['due_date'])
    upcoming_payments = upcoming_payments_list[:5]

    import json
    from django.core.serializers.json import DjangoJSONEncoder

    context = {
        'total_students': total_students,
        'total_pending_amount': total_pending_amount,
        'active_trainers': active_trainers,
        'placement_rate': round(placement_rate, 1),
        'weekly_students': weekly_students,
        'weekly_payments': weekly_payments,
        'monthly_pending': json.dumps(monthly_pending_data, cls=DjangoJSONEncoder),
        'enrollment_data': json.dumps(enrollment_data, cls=DjangoJSONEncoder),
        'recent_activities': recent_activities,
        'recent_students': recent_students,
        'upcoming_payments': upcoming_payments,
    }
    return render(request, 'accounts/admin_dashboard.html', context)

@login_required
@user_passes_test(is_staff)
def staff_dashboard(request):
    # Basic Statistics
    total_students = Student.objects.count()
    total_pending_amount = Payment.objects.aggregate(total_pending=Sum('total_pending_amount'))['total_pending'] or 0
    active_trainers = Trainer.objects.count()  # Count all trainers since there's no active status

    # Get placement rate using course_status field
    total_completed = Student.objects.filter(course_status='C').count()
    total_placed = Student.objects.filter(course_status='P').count()
    placement_rate = (total_placed / total_completed * 100) if total_completed > 0 else 0

    # Monthly student enrollment
    now = timezone.now()
    six_months_ago = now - timedelta(days=180)
    monthly_enrollments = (
        Student.objects
        .filter(enrollment_date__gte=six_months_ago)
        .annotate(month=TruncMonth('enrollment_date'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )

    enrollment_data = [
        {'month': item['month'].strftime('%Y-%m'), 'count': item['count']}
        for item in monthly_enrollments
    ]

    # Monthly pending amounts for the last 6 months
    monthly_pending_data = {}
    
    # Initialize months to ensure all 6 months are present in the chart
    current_date = now.date()
    for _ in range(6):
        month_key = current_date.strftime('%Y-%m')
        monthly_pending_data[month_key] = 0
        # Go to the first day of the current month, then subtract one day to get the last day of the previous month
        first_day_of_month = current_date.replace(day=1)
        current_date = first_day_of_month - timedelta(days=1)

    pending_payments = Payment.objects.filter(total_pending_amount__gt=0)

    for payment in pending_payments:
        for i in range(1, 5):
            due_date = getattr(payment, f'emi_{i}_date')
            amount = getattr(payment, f'emi_{i}_amount')
            paid_amount = getattr(payment, f'emi_{i}_paid_amount')

            if due_date and amount and not paid_amount and six_months_ago.date() <= due_date <= now.date():
                month_key = due_date.strftime('%Y-%m')
                if month_key in monthly_pending_data:
                    monthly_pending_data[month_key] += float(amount)

    monthly_pending_data = [
        {'month': key, 'amount': value}
        for key, value in sorted(monthly_pending_data.items())
    ]

    # Weekly Statistics
    one_week_ago = now - timedelta(days=7)
    weekly_students = Student.objects.filter(enrollment_date__gte=one_week_ago).count()
    weekly_payments = Payment.objects.filter(student__enrollment_date__gte=one_week_ago).aggregate(
        total=Sum('amount_paid')
    )['total'] or 0

    # Recent Activities and Students
    recent_activities = TransactionLog.objects.order_by('-timestamp')[:10]
    recent_students = Student.objects.order_by('-enrollment_date')[:5]
    
    # Fetch upcoming payments
    pending_payments = Payment.objects.filter(total_pending_amount__gt=0).select_related('student', 'student__consultant')

    # Get all unique course IDs from the students in pending payments
    student_course_ids = [p.student.course_id for p in pending_payments if p.student and p.student.course_id]
    
    # Fetch all relevant courses in a single query
    from coursedb.models import Course
    courses = Course.objects.filter(id__in=student_course_ids)
    course_map = {course.id: course.course_name for course in courses}

    upcoming_payments_list = []
    today = timezone.now().date()

    for payment in pending_payments:
        for i in range(1, 5):
            due_date = getattr(payment, f'emi_{i}_date')
            amount = getattr(payment, f'emi_{i}_amount')
            paid_amount = getattr(payment, f'emi_{i}_paid_amount')

            if due_date and amount and not paid_amount:
                total_paid_by_student = payment.amount_paid or 0
                for j in range(1, 5):
                    total_paid_by_student += getattr(payment, f'emi_{j}_paid_amount') or 0

                course_name = course_map.get(payment.student.course_id, 'N/A') if payment.student else 'N/A'

                upcoming_payments_list.append({
                    'student_id': payment.student.student_id,
                    'student_name': f"{payment.student.first_name} {payment.student.last_name or ''}",
                    'mobile': payment.student.phone,
                    'course': course_name,
                    'consultant': payment.student.consultant.name if payment.student.consultant else 'N/A',
                    'emi_number': i,
                    'course_fee': payment.total_fees or 0,
                    'amount': amount,
                    'paid': total_paid_by_student,
                    'due_date': due_date,
                })
                break
    # Sort all upcoming payments by due date and take the first 5.
    upcoming_payments_list.sort(key=lambda x: x['due_date'])
    upcoming_payments = upcoming_payments_list[:5]

    import json
    from django.core.serializers.json import DjangoJSONEncoder

    context = {
        'total_students': total_students,
        'total_pending_amount': total_pending_amount,
        'active_trainers': active_trainers,
        'placement_rate': round(placement_rate, 1),
        'weekly_students': weekly_students,
        'weekly_payments': weekly_payments,
        'monthly_pending': json.dumps(monthly_pending_data, cls=DjangoJSONEncoder),
        'enrollment_data': json.dumps(enrollment_data, cls=DjangoJSONEncoder),
        'recent_activities': recent_activities,
        'recent_students': recent_students,
        'upcoming_payments': upcoming_payments,
    }
    return render(request, 'accounts/staff_dashboard.html', context)

@login_required
@user_passes_test(is_consultant)
def consultant_dashboard(request):
    now = timezone.now()
    
    # Get all batches with related data
    all_batches_for_stats = Batch.objects.all()
    active_batches = all_batches_for_stats.filter(batch_status__in=['IP', 'YTS']).select_related('course', 'trainer').prefetch_related('students').order_by('end_date')
    
    # Prepare batches data for the dashboard
    batches_data = []
    for batch in active_batches:
        # Calculate progress based on start and end dates
        if batch.start_date and batch.end_date:
            total_days = (batch.end_date - batch.start_date).days
            days_passed = (now.date() - batch.start_date).days
            
            if total_days > 0:
                progress = min(100, max(0, int((days_passed / total_days) * 100)))
            else:
                progress = 0
        else:
            progress = 0
            
        # Format batch data
        batch_data = {
            'id': batch.id,
            'batch_id': batch.batch_id,
            'course': batch.course.course_name if batch.course else "N/A",
            'trainer': {
                'id': batch.trainer.id if batch.trainer else None,
                'name': batch.trainer.name if batch.trainer else "N/A",
                'initials': ''.join([name[0].upper() for name in batch.trainer.name.split()[:2]]) if batch.trainer else "NA"
            },
            'startDate': batch.start_date.isoformat() if batch.start_date else None,
            'endDate': batch.end_date.isoformat() if batch.end_date else None,
            'status': batch.batch_status.lower() if batch.batch_status else "unknown",
            'progress': batch.batch_percentage if batch.batch_percentage is not None else progress,
            'batchType': batch.batch_type if batch.batch_type else "Regular",
            'students': batch.batchstudent_set.filter(is_active=True).count(),
            'hoursPerDay': batch.hours_per_day if batch.hours_per_day else 0,
            'days': batch.days.split(',') if batch.days and isinstance(batch.days, str) else (batch.days if isinstance(batch.days, list) else []),
            'startTime': batch.start_time.strftime('%H:%M') if batch.start_time else None,
            'endTime': batch.end_time.strftime('%H:%M') if batch.end_time else None
        }
        batches_data.append(batch_data)
    # Create calendar events for all batches
    calendar_events = []
    for batch in active_batches:
        if batch.start_date:
            calendar_events.append({
                'title': f'{batch.batch_id}: {batch.course.course_name if batch.course else ""} (Start)',
                'start': batch.start_date.isoformat(),
                'backgroundColor': '#34d3ff',
                'borderColor': '#34d3ff'
            })
        
        if batch.end_date:
            calendar_events.append({
                'title': f'{batch.batch_id}: {batch.course.course_name if batch.course else ""} (End)',
                'start': batch.end_date.isoformat(),
                'backgroundColor': '#8b5cf6',
                'borderColor': '#8b5cf6'
            })
    
    # Get trainer handovers for notifications
    from batchdb.models import TrainerHandover
    handovers = TrainerHandover.objects.select_related('batch', 'from_trainer', 'to_trainer').order_by('-requested_at')[:5]
    
    notifications_data = []
    for handover in handovers:
        notifications_data.append({
            'id': handover.id,
            'content': f"Batch {handover.batch.batch_id} transferred from {handover.from_trainer.name} to {handover.to_trainer.name}",
            'time': f"{(now - handover.requested_at).days} days ago" if (now - handover.requested_at).days > 0 else "Today",
            'read': False
        })
    
    # Add notifications for batches nearing completion (>80%)
    for batch in active_batches:
        if batch.batch_status == 'IP' and batch.batch_percentage and batch.batch_percentage >= 80:
            notifications_data.append({
                'id': f"batch_{batch.id}",
                'content': f"Batch {batch.batch_id} is {batch.batch_percentage}% complete",
                'time': "Recently updated",
                'read': False
            })
    
    import json
    from django.core.serializers.json import DjangoJSONEncoder
    
    trainers = Trainer.objects.all()
    trainers_data = [{'id': t.id, 'name': t.name} for t in trainers]

    if hasattr(request.user, 'consultant_profile'):
        # Consultant user → only their data
        consultant = request.user.consultant_profile.consultant
        total_students = Student.objects.filter(consultant=consultant).count()
    elif request.user.is_superuser:
        # Super admin → all data
        total_students = Student.objects.all().count()
    else:
        total_students = 0

    context = {
        'total_students': total_students,
        'total_batches': all_batches_for_stats.count(),
        'yts_batches': all_batches_for_stats.filter(batch_status='YTS').count(),
        'in_progress_batches': all_batches_for_stats.filter(batch_status='IP').count(),
        'completed_batches': all_batches_for_stats.filter(batch_status='C').count(),
        'total_trainers': trainers.count(),
        'handovers': handovers.count(),
        'trainers': trainers,
        'batches_data': json.dumps(batches_data, cls=DjangoJSONEncoder),
        'trainers_data': json.dumps(trainers_data, cls=DjangoJSONEncoder),
        'notifications_data': json.dumps(notifications_data, cls=DjangoJSONEncoder),
        'calendar_events': json.dumps(calendar_events, cls=DjangoJSONEncoder),
    }
    return render(request, 'accounts/consultant_dashboard.html', context)

@login_required
@user_passes_test(is_trainer)
def trainer_dashboard(request):
    now = timezone.now()
    
    trainer = request.user.trainer_profile.trainer
    
    # Get all batches for the specific trainer
    all_batches_for_stats = Batch.objects.filter(trainer=trainer)
    active_batches = all_batches_for_stats.filter(batch_status__in=['IP', 'YTS']).select_related('course').prefetch_related('students').order_by('end_date')
    
    # Prepare batches data for the dashboard
    batches_data = []
    for batch in active_batches:
        # Calculate progress based on start and end dates
        if batch.start_date and batch.end_date:
            total_days = (batch.end_date - batch.start_date).days
            days_passed = (now.date() - batch.start_date).days
            
            if total_days > 0:
                progress = min(100, max(0, int((days_passed / total_days) * 100)))
            else:
                progress = 0
        else:
            progress = 0
            
        # Format batch data
        batch_data = {
            'id': batch.id,
            'batch_id': batch.batch_id,
            'course': batch.course.course_name if batch.course else "N/A",
            'trainer': {
                'id': batch.trainer.id if batch.trainer else None,
                'name': batch.trainer.name if batch.trainer else "N/A",
                'initials': ''.join([name[0].upper() for name in batch.trainer.name.split()[:2]]) if batch.trainer else "NA"
            },
            'startDate': batch.start_date.isoformat() if batch.start_date else None,
            'endDate': batch.end_date.isoformat() if batch.end_date else None,
            'status': batch.batch_status.lower() if batch.batch_status else "unknown",
            'progress': batch.batch_percentage if batch.batch_percentage is not None else progress,
            'batchType': batch.batch_type if batch.batch_type else "Regular",
            'students': batch.batchstudent_set.filter(is_active=True).count(),
            'hoursPerDay': batch.hours_per_day if batch.hours_per_day else 0,
            'days': batch.days.split(',') if batch.days and isinstance(batch.days, str) else (batch.days if isinstance(batch.days, list) else []),
            'startTime': batch.start_time.strftime('%H:%M') if batch.start_time else None,
            'endTime': batch.end_time.strftime('%H:%M') if batch.end_time else None
        }
        batches_data.append(batch_data)

    # Create calendar events for all batches
    calendar_events = []
    for batch in active_batches:
        if batch.start_date:
            calendar_events.append({
                'title': f'{batch.batch_id}: {batch.course.course_name if batch.course else ""} (Start)',
                'start': batch.start_date.isoformat(),
                'backgroundColor': '#34d3ff',
                'borderColor': '#34d3ff'
            })
        
        if batch.end_date:
            calendar_events.append({
                'title': f'{batch.batch_id}: {batch.course.course_name if batch.course else ""} (End)',
                'start': batch.end_date.isoformat(),
                'backgroundColor': '#8b5cf6',
                'borderColor': '#8b5cf6'
            })
    
    # Get trainer handovers for notifications
    from batchdb.models import TrainerHandover
    handovers = TrainerHandover.objects.filter(to_trainer=trainer).select_related('batch', 'from_trainer', 'to_trainer').order_by('-requested_at')[:5]
    
    notifications_data = []
    for handover in handovers:
        notifications_data.append({
            'id': handover.id,
            'content': f"Batch {handover.batch.batch_id} transferred from {handover.from_trainer.name} to you",
            'time': f"{(now - handover.requested_at).days} days ago" if (now - handover.requested_at).days > 0 else "Today",
            'read': False
        })
    
    # Add notifications for batches nearing completion (>80%)
    for batch in active_batches:
        if batch.batch_status == 'IP' and batch.batch_percentage and batch.batch_percentage >= 80:
            notifications_data.append({
                'id': f"batch_{batch.id}",
                'content': f"Batch {batch.batch_id} is {batch.batch_percentage}% complete",
                'time': "Recently updated",
                'read': False
            })

    import json
    from django.core.serializers.json import DjangoJSONEncoder

    context = {
        'total_batches': all_batches_for_stats.count(),
        'yts_batches': all_batches_for_stats.filter(batch_status='YTS').count(),
        'in_progress_batches': all_batches_for_stats.filter(batch_status='IP').count(),
        'completed_batches': all_batches_for_stats.filter(batch_status='C').count(),
        'handovers': handovers.count(),
        'batches_data': json.dumps(batches_data, cls=DjangoJSONEncoder),
        'notifications_data': json.dumps(notifications_data, cls=DjangoJSONEncoder),
        'calendar_events': json.dumps(calendar_events, cls=DjangoJSONEncoder),
    }
    return render(request, 'accounts/trainer_dashboard.html', context)

@login_required
@user_passes_test(is_placement)
def placement_dashboard(request):
    # Base Querysets
    students_in_pool = Student.objects.filter(pl_required=True)
    placements = Placement.objects.filter(student__in=students_in_pool)
    drives = Company.objects.all()
    
    # Resume Shared Status Counts
    from placementdrive.models import ResumeSharedStatus
    total_resume_shared = ResumeSharedStatus.objects.count()
    position_closed_count = ResumeSharedStatus.objects.filter(status='position_closed').count()
    not_shortlisted_count = ResumeSharedStatus.objects.filter(status='not_shortlisted').count()
    no_response_count = ResumeSharedStatus.objects.filter(status='no_response').count()
    moved_to_interview_count = ResumeSharedStatus.objects.filter(status='interview_stage').count()
    pending_count = total_resume_shared - (position_closed_count + not_shortlisted_count + no_response_count + moved_to_interview_count)

    # Overall Stats
    total_placement_pool = placements.count()
    total_placed = placements.filter(student__course_status='P').count()
    
    # Actively seeking students for the main stat card
    actively_seeking_stat = placements.filter(is_active=True)
    
    # Separate counts for actively seeking
    actively_seeking_completed = actively_seeking_stat.filter(student__course_status='C').count()
    actively_seeking_in_progress = actively_seeking_stat.filter(student__course_status='IP').count()
    actively_seeking_yts = actively_seeking_stat.filter(student__course_status='YTS').count()
    
    actively_seeking_count = actively_seeking_stat.count()
    
    placement_rate = ((total_placed / total_placement_pool) * 100) if total_placement_pool > 0 else 0
    active_drives_count = drives.count()
    
    # Correctly count scheduled and completed interviews
    interviews_scheduled = Company.objects.filter(progress='interview_scheduling').count()
    interviews_completed_count = Company.objects.filter(progress='interview_completed').count()
    onboarding_call_done_count = Student.objects.filter(onboardingcalldone=True).count()
    interview_questions_shared_count = Student.objects.filter(interviewquestion_shared=True).count()
    resume_templates_shared_count = Student.objects.filter(resume_template_shared=True).count()

    # New stats for mock interviews, placement sessions, and certificates
    mock_interviews_completed_count = Student.objects.filter(mock_interview_completed=True).count()
    placement_sessions_completed_count = Student.objects.filter(placement_session_completed=True).count()
    certificates_issued_count = Student.objects.filter(certificate_issued=True).count()

    # --- Refined Resume Statistics ---
    # 1. Start with students who need placement and are in an active course status.
    #    Exclude any who are explicitly marked as inactive in the placement table.
    active_pool_for_resumes = Student.objects.filter(
        pl_required=True,
        course_status__in=['IP', 'C', 'YTS']
    ).exclude(placement__is_active=False)

    # 2. From this pool, find those who don't have a resume.
    students_no_resume = active_pool_for_resumes.filter(
        Q(placement__isnull=True) | Q(placement__resume_link__isnull=True) | Q(placement__resume_link='')
    )
    
    # 3. Calculate the total and segregated counts.
    students_no_resume_list = students_no_resume.select_related('placement')
    
    resumes_to_collect_count = students_no_resume_list.count()
    
    completed_but_no_resume_list = students_no_resume_list.filter(course_status='C')
    in_progress_80_99_no_resume_list = students_no_resume_list.filter(course_status='IP', course_percentage__gte=80, course_percentage__lt=99)
    in_progress_50_80_no_resume_list = students_no_resume_list.filter(course_status='IP', course_percentage__gte=50, course_percentage__lt=80)
    in_progress_below_50_no_resume_list = students_no_resume_list.filter(course_status='IP', course_percentage__lt=50)
    yts_no_resume_list = students_no_resume_list.filter(course_status='YTS')

    completed_but_no_resume = completed_but_no_resume_list.count()
    in_progress_80_99_no_resume = in_progress_80_99_no_resume_list.count()
    in_progress_50_80_no_resume = in_progress_50_80_no_resume_list.count()
    in_progress_below_50_no_resume = in_progress_below_50_no_resume_list.count()
    yts_no_resume = yts_no_resume_list.count()

    # --- Pagination for Resume Lists ---
    def paginate_queryset(queryset, page_param, per_page=10):
        paginator = Paginator(queryset, per_page)
        page_number = request.GET.get(page_param)
        try:
            return paginator.page(page_number)
        except PageNotAnInteger:
            return paginator.page(1)
        except EmptyPage:
            return paginator.page(paginator.num_pages)

    completed_paginated = paginate_queryset(completed_but_no_resume_list, 'completed_page')
    progress_80_99_paginated = paginate_queryset(in_progress_80_99_no_resume_list, 'progress_80_99_page')
    progress_50_80_paginated = paginate_queryset(in_progress_50_80_no_resume_list, 'progress_50_80_page')
    progress_below_50_paginated = paginate_queryset(in_progress_below_50_no_resume_list, 'progress_below_50_page')
    yts_paginated = paginate_queryset(yts_no_resume_list, 'yts_page')


    # Table Data
    recently_placed_students = students_in_pool.filter(course_status='P').order_by('-end_date')[:5]
    
    # Manually fetch courses for all student lists
    from coursedb.models import Course
    
    # Collect all course_ids from all relevant student querysets
    all_student_lists = [
        recently_placed_students,
        completed_but_no_resume_list,
        in_progress_80_99_no_resume_list,
        in_progress_50_80_no_resume_list,
        in_progress_below_50_no_resume_list,
        yts_no_resume_list
    ]
    
    all_course_ids = set()
    for student_list in all_student_lists:
        for student in student_list:
            if student.course_id:
                all_course_ids.add(student.course_id)
    
    courses_dict = {c.id: c.course_name for c in Course.objects.filter(id__in=list(all_course_ids))}
    # Fetch upcoming interviews using the correct 'Interview' model from 'placementdrive'
    from placementdrive.models import Interview

    from django.db.models import Max
    # Get the latest interview round for each company without using DISTINCT ON
    upcoming_interviews = Interview.objects.filter(
        interview_date__gte=timezone.now().date()
    ).annotate(
        latest_round=Max('company__scheduled_interviews__round_number')
    ).filter(
        round_number=F('latest_round')
    ).select_related('company').prefetch_related('student_status__student').order_by('interview_date')[:5]
    students_yet_to_be_placed = placements.filter(is_active=True, student__course_status__in=['IP', 'C', 'YTS', 'H']).select_related('student')[:10]

    context = {
        # Stat Cards
        'total_placement_pool': total_placement_pool,
        'actively_seeking': actively_seeking_count,
        'actively_seeking_completed': actively_seeking_completed,
        'actively_seeking_in_progress': actively_seeking_in_progress,
        'actively_seeking_yts':actively_seeking_yts,
        'total_placed': total_placed,
        'placement_rate': round(placement_rate, 1),
        'active_drives_count': active_drives_count,
        'interviews_scheduled': interviews_scheduled,
        'interviews_completed': interviews_completed_count,
        'onboarding_call_done_count': onboarding_call_done_count,
        'interview_questions_shared_count': interview_questions_shared_count,
        'resume_templates_shared_count': resume_templates_shared_count,
        'mock_interviews_completed': mock_interviews_completed_count,
        'placement_sessions_completed': placement_sessions_completed_count,
        'certificates_issued': certificates_issued_count,
        
        # Resume Shared Status Counts
        'total_resume_shared': total_resume_shared,
        'position_closed_count': position_closed_count,
        'not_shortlisted_count': not_shortlisted_count,
        'no_response_count': no_response_count,
        'pending_count': pending_count,
        'moved_to_interview_count': moved_to_interview_count,

        # Resume Stats (Counts)
        'resumes_to_collect_count': resumes_to_collect_count,
        'completed_but_no_resume': completed_but_no_resume,
        'in_progress_80_99_no_resume': in_progress_80_99_no_resume,
        'in_progress_50_80_no_resume': in_progress_50_80_no_resume,
        'in_progress_below_50_no_resume': in_progress_below_50_no_resume,
        'yts_no_resume': yts_no_resume,

        # Paginated Lists for Tables
        'completed_list_paginated': completed_paginated,
        'progress_80_99_list_paginated': progress_80_99_paginated,
        'progress_50_80_list_paginated': progress_50_80_paginated,
        'progress_below_50_list_paginated': progress_below_50_paginated,
        'yts_list_paginated': yts_paginated,

        # Other Tables
        'recently_placed': recently_placed_students,
        'courses_dict': courses_dict,
        'upcoming_interviews': upcoming_interviews,
        'students_yet_to_be_placed': students_yet_to_be_placed,
    }
    return render(request, 'accounts/placement_dashboard.html', context)

@login_required
@user_passes_test(is_batch_coordinator)
def batch_coordination_dashboard(request):
    now = timezone.now()
    
    # Get all batches with related data
    all_batches_for_stats = Batch.objects.all()
    active_batches = all_batches_for_stats.filter(batch_status__in=['IP', 'YTS']).select_related('course', 'trainer').prefetch_related('students').order_by('end_date')
    
    # Prepare batches data for the dashboard
    batches_data = []
    for batch in active_batches:
        # Calculate progress based on start and end dates
        if batch.start_date and batch.end_date:
            total_days = (batch.end_date - batch.start_date).days
            days_passed = (now.date() - batch.start_date).days
            
            if total_days > 0:
                progress = min(100, max(0, int((days_passed / total_days) * 100)))
            else:
                progress = 0
        else:
            progress = 0
            
        # Format batch data
        batch_data = {
            'id': batch.id,
            'batch_id': batch.batch_id,
            'course': batch.course.course_name if batch.course else "N/A",
            'trainer': {
                'id': batch.trainer.id if batch.trainer else None,
                'name': batch.trainer.name if batch.trainer else "N/A",
                'initials': ''.join([name[0].upper() for name in batch.trainer.name.split()[:2]]) if batch.trainer else "NA"
            },
            'startDate': batch.start_date.isoformat() if batch.start_date else None,
            'endDate': batch.end_date.isoformat() if batch.end_date else None,
            'status': batch.batch_status.lower() if batch.batch_status else "unknown",
            'progress': batch.batch_percentage if batch.batch_percentage is not None else progress,
            'batchType': batch.batch_type if batch.batch_type else "Regular",
            'students': batch.batchstudent_set.filter(is_active=True).count(),
            'hoursPerDay': batch.hours_per_day if batch.hours_per_day else 0,
            'days': batch.days.split(',') if batch.days and isinstance(batch.days, str) else (batch.days if isinstance(batch.days, list) else []),
            'startTime': batch.start_time.strftime('%H:%M') if batch.start_time else None,
            'endTime': batch.end_time.strftime('%H:%M') if batch.end_time else None
        }
        batches_data.append(batch_data)
    # Create calendar events for all batches
    calendar_events = []
    for batch in active_batches:
        if batch.start_date:
            calendar_events.append({
                'title': f'{batch.batch_id}: {batch.course.course_name if batch.course else ""} (Start)',
                'start': batch.start_date.isoformat(),
                'backgroundColor': '#34d3ff',
                'borderColor': '#34d3ff'
            })
        
        if batch.end_date:
            calendar_events.append({
                'title': f'{batch.batch_id}: {batch.course.course_name if batch.course else ""} (End)',
                'start': batch.end_date.isoformat(),
                'backgroundColor': '#8b5cf6',
                'borderColor': '#8b5cf6'
            })
    
    # Get trainer handovers for notifications
    from batchdb.models import TrainerHandover
    handovers = TrainerHandover.objects.select_related('batch', 'from_trainer', 'to_trainer').order_by('-requested_at')[:5]
    
    notifications_data = []
    for handover in handovers:
        notifications_data.append({
            'id': handover.id,
            'content': f"Batch {handover.batch.batch_id} transferred from {handover.from_trainer.name} to {handover.to_trainer.name}",
            'time': f"{(now - handover.requested_at).days} days ago" if (now - handover.requested_at).days > 0 else "Today",
            'read': False
        })
    
    # Add notifications for batches nearing completion (>80%)
    for batch in active_batches:
        if batch.batch_status == 'IP' and batch.batch_percentage and batch.batch_percentage >= 80:
            notifications_data.append({
                'id': f"batch_{batch.id}",
                'content': f"Batch {batch.batch_id} is {batch.batch_percentage}% complete",
                'time': "Recently updated",
                'read': False
            })
    
    import json
    from django.core.serializers.json import DjangoJSONEncoder
    
    trainers = Trainer.objects.all()
    trainers_data = [{'id': t.id, 'name': t.name} for t in trainers]
    
    context = {
        'total_students': Student.objects.count(),
        'total_batches': all_batches_for_stats.count(),
        'yts_batches': all_batches_for_stats.filter(batch_status='YTS').count(),
        'in_progress_batches': all_batches_for_stats.filter(batch_status='IP').count(),
        'completed_batches': all_batches_for_stats.filter(batch_status='C').count(),
        'total_trainers': trainers.count(),
        'handovers': handovers.count(),
        'trainers': trainers,
        'batches_data': json.dumps(batches_data, cls=DjangoJSONEncoder),
        'trainers_data': json.dumps(trainers_data, cls=DjangoJSONEncoder),
        'notifications_data': json.dumps(notifications_data, cls=DjangoJSONEncoder),
        'calendar_events': json.dumps(calendar_events, cls=DjangoJSONEncoder),
    }
    return render(request, 'accounts/batch_coordination_dashboard.html', context)

@user_passes_test(is_admin)
def user_list(request):
    users = CustomUser.objects.all().order_by('name')
    return render(request, 'accounts/user_list.html', {'users': users})

@user_passes_test(is_admin)
def create_user(request):
    if request.method == 'POST':
        form = UserForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, "User created successfully.")
            return redirect('user_list')
    else:
        form = UserForm()
    return render(request, 'accounts/create_user.html', {'form': form})

@login_required
def update_user(request, pk):
    user_to_update = get_object_or_404(CustomUser, pk=pk)
    
    # Admins can edit any user, other roles can only edit their own profile
    if not request.user.role == 'admin' and request.user.pk != user_to_update.pk:
        messages.error(request, "You don't have permission to edit this profile.")
        # Redirect to a safe page, e.g., their own dashboard
        if request.user.role == 'staff':
            return redirect('staff_dashboard')
        elif request.user.role == 'consultant':
            return redirect('consultant_dashboard')
        elif request.user.role == 'batch_coordination':
            return redirect('batch_coordination_dashboard')
        else:
            return redirect('login') # Fallback

    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=user_to_update, user=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            # Redirect based on user role
            if user_to_update.role == 'admin':
                return redirect('admin_dashboard')
            elif user_to_update.role == 'staff':
                return redirect('staff_dashboard')
            elif user_to_update.role == 'consultant':
                return redirect('consultant_dashboard')
            elif user_to_update.role == 'batch_coordination':
                return redirect('batch_coordination_dashboard')
            elif user_to_update.role == 'placement':
                return redirect('placement_dashboard')
            else:
                # Fallback for any other roles or if role is not set
                return redirect('user_list')
    else:
        form = UserUpdateForm(instance=user_to_update, user=request.user)

    # Flag to check if the user is editing their own profile
    is_editing_own_profile = request.user.pk == user_to_update.pk

    context = {
        'form': form,
        'user': user_to_update,
        'is_editing_own_profile': is_editing_own_profile
    }
    return render(request, 'accounts/update_user.html', context)

@user_passes_test(is_admin)
def delete_user(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    if request.method == 'POST':
        user.delete()
        messages.success(request, "User deleted successfully.")
        return redirect('user_list')
    return render(request, 'accounts/delete_user_confirm.html', {'user': user})
from django.contrib.auth import logout, authenticate, login
from .forms import EmailAuthenticationForm

def login_view(request):
    if request.method == 'POST':
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(request, username=email, password=password)
            if user is not None:
                try:
                    user_settings = UserSettings.objects.get(user=user)
                    if user_settings.enable_2fa:
                        request.session['2fa_user_id'] = user.id
                        return redirect('verify_2fa')
                except UserSettings.DoesNotExist:
                    pass  # No settings, so no 2FA

                login(request, user)
                if user.role == 'admin':
                    return redirect('admin_dashboard')
                elif user.role == 'consultant':
                    return redirect('consultant_dashboard')
                elif user.role == 'trainer':
                    return redirect('trainer_dashboard')
                elif user.role == 'placement':
                    return redirect('placement_dashboard')
                elif user.role == 'batch_coordination':
                    return redirect('batch_coordination_dashboard')
                else:
                    return redirect('staff_dashboard')
            else:
                messages.error(request, "Invalid email or password.")
        else:
            messages.error(request, "Invalid email or password.")
    else:
        form = EmailAuthenticationForm()
    return render(request, 'accounts/login.html', {'form': form})

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect('login')

@login_required
def password_change(request):
    if request.method == 'POST':
        form = PasswordChangeForm(request.user, request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Your password has been changed successfully.")
            if request.user.role == 'admin':
                return redirect('admin_dashboard')
            elif request.user.role == 'consultant':
                return redirect('consultant_dashboard')
            elif request.user.role == 'batch_coordination':
                return redirect('batch_coordination_dashboard')
            else:
                return redirect('staff_dashboard')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/password_change.html', {'form': form})

import random
import string
from django.conf import settings
from datetime import timedelta
from .utils import send_otp_email

def password_reset_request(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = CustomUser.objects.get(email=email)
        except CustomUser.DoesNotExist:
            messages.error(request, "User with this email does not exist.")
            return render(request, 'accounts/password_reset_request.html')

        otp = ''.join(random.choices(string.digits, k=6))
        request.session['otp'] = otp
        request.session['otp_expiry'] = (timezone.now() + timedelta(minutes=3)).isoformat()
        request.session['reset_email'] = email

        send_otp_email(email, otp)
        
        messages.success(request, "An OTP has been sent to your email.")
        request.session['otp_page_visited'] = False  # Flag for initial visit
        return redirect('password_reset_otp')

    return render(request, 'accounts/password_reset_request.html')

def password_reset_otp(request):
    # Security enhancement: Invalidate session on refresh/re-navigation
    if request.method == 'GET':
        if request.session.get('otp_page_visited', True): # Default to True to be safe
            # If the flag is True, it's a refresh. Terminate.
            if 'otp' in request.session: del request.session['otp']
            if 'otp_expiry' in request.session: del request.session['otp_expiry']
            if 'reset_email' in request.session: del request.session['reset_email']
            messages.error(request, "For security, the password reset process has been terminated. Please start over.")
            return redirect('password_reset_request')
        else:
            # First visit, set the flag to True
            request.session['otp_page_visited'] = True
            return render(request, 'accounts/password_reset_otp.html')

    if request.method == 'POST':
        otp_entered = request.POST.get('otp')
        otp_session = request.session.get('otp')
        otp_expiry_str = request.session.get('otp_expiry')

        if not otp_session or not otp_expiry_str:
            messages.error(request, "OTP has expired. Please request a new one.")
            return redirect('password_reset_request')

        otp_expiry = timezone.datetime.fromisoformat(otp_expiry_str)

        if timezone.now() > otp_expiry:
            messages.error(request, "OTP has expired. Please request a new one.")
            # Clear the expired OTP from the session
            del request.session['otp']
            del request.session['otp_expiry']
            return redirect('password_reset_request')

        if otp_entered == otp_session:
            # OTP is correct, clear it from session and proceed to new password form
            del request.session['otp']
            del request.session['otp_expiry']
            request.session['reset_otp_verified'] = True
            request.session['new_password_page_visited'] = False # Flag for initial visit
            return redirect('password_reset_new_password')
        else:
            messages.error(request, "Invalid OTP.")
            return render(request, 'accounts/password_reset_otp.html')


def password_reset_new_password(request):
    # Security enhancement: Invalidate session on refresh/re-navigation
    if request.method == 'GET':
        if request.session.get('new_password_page_visited', True): # Default to True to be safe
            # If the flag is True, it's a refresh. Terminate.
            if 'reset_otp_verified' in request.session: del request.session['reset_otp_verified']
            if 'reset_email' in request.session: del request.session['reset_email']
            messages.error(request, "For security, the password reset process has been terminated. Please start over.")
            return redirect('password_reset_request')
        else:
            # First visit, set the flag to True
            request.session['new_password_page_visited'] = True
            # We need to pass the form to the template on the first GET request
            email = request.session.get('reset_email')
            if not email:
                messages.error(request, "Something went wrong. Please start over.")
                return redirect('password_reset_request')
            try:
                user = CustomUser.objects.get(email=email)
            except CustomUser.DoesNotExist:
                messages.error(request, "User not found.")
                return redirect('password_reset_request')
            form = PasswordResetForm(user)
            return render(request, 'accounts/password_reset_new_password.html', {'form': form})

    if not request.session.get('reset_otp_verified'):
        messages.error(request, "Please verify your OTP first.")
        return redirect('password_reset_request')

    email = request.session.get('reset_email')
    if not email:
        messages.error(request, "Something went wrong. Please start over.")
        return redirect('password_reset_request')

    try:
        user = CustomUser.objects.get(email=email)
    except CustomUser.DoesNotExist:
        messages.error(request, "User not found.")
        return redirect('password_reset_request')

    if request.method == 'POST':
        form = PasswordResetForm(user, request.POST)
        if form.is_valid():
            form.save()
            # Clean up session variables
            del request.session['reset_email']
            del request.session['reset_otp_verified']
            messages.success(request, "Your password has been reset successfully. Please log in.")
            return redirect('login')
    else:
        form = PasswordResetForm(user)

    return render(request, 'accounts/password_reset_new_password.html', {'form': form})

def verify_2fa(request):
    user_id = request.session.get('2fa_user_id')
    if not user_id:
        return redirect('login')

    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        return redirect('login')

    if request.method == 'POST':
        form = TwoFactorForm(request.POST)
        if form.is_valid():
            otp = form.cleaned_data.get('otp')
            totp = pyotp.TOTP(user.totp_secret)
            if totp.verify(otp):
                login(request, user)
                del request.session['2fa_user_id']
                if user.role == 'admin':
                    return redirect('admin_dashboard')
                elif user.role == 'consultant':
                    return redirect('consultant_dashboard')
                elif user.role == 'trainer':
                    return redirect('trainer_dashboard')
                elif user.role == 'placement':
                    return redirect('placement_dashboard')
                elif user.role == 'batch_coordination':
                    return redirect('batch_coordination_dashboard')
                else:
                    return redirect('staff_dashboard')
            else:
                messages.error(request, "Invalid one-time password.")
    else:
        form = TwoFactorForm()

    return render(request, 'accounts/verify_2fa.html', {'form': form})
from django.http import JsonResponse

def trainers_availabity(request):
    trainers = Trainer.objects.all()
    
    trainers_data = []
    for trainer in trainers:
        trainers_data.append({
            'id': trainer.id,
            'name': trainer.name,
            'trainer_id': trainer.trainer_id,
        })
    
    return JsonResponse(trainers_data, safe=False)

from django.http import JsonResponse
from datetime import datetime

def trainer_availability_api(request):
    trainer_id = request.GET.get('trainer_id')
    try:
        trainer = Trainer.objects.get(id=trainer_id)
        
        # Get all batches for statistics
        all_batches = Batch.objects.filter(trainer=trainer)
        
        # Calculate batch counts
        total_batches = all_batches.count()
        completed_batches = all_batches.filter(batch_status='C').count()
        ongoing_batches = all_batches.filter(batch_status='IP').count()
        yts_batches = all_batches.filter(batch_status='YTS').count()

        # Filter for active batches for slot checking
        active_batches = all_batches.filter(batch_status__in=['IP', 'YTS'])

        availability_data = []
        occupied_count = 0

        for slot in trainer.timing_slots:
            slot_start = datetime.strptime(slot['start_time'], "%H:%M").time()
            slot_end = datetime.strptime(slot['end_time'], "%H:%M").time()

            batch = active_batches.filter(start_time=slot_start, end_time=slot_end).first()

            if batch:
                occupied_count += 1
                availability_data.append({
                    'slot_time': f"{batch.start_time.strftime('%I:%M %p')} - {batch.end_time.strftime('%I:%M %p')}",
                    'course_name': batch.course.course_name if batch.course else "N/A",
                    'batch_id': batch.batch_id,
                    'current_module': "Not specified",
                    'end_date': batch.end_date.strftime('%d %b %Y') if batch.end_date else "N/A",
                    'status': 'Occupied',
                    'availability': slot.get('availability', 'N/A'),
                    'mode': slot.get('mode', 'N/A'),
                    'percentage': batch.batch_percentage if batch.batch_percentage is not None else 0,
                })
            else:
                availability_data.append({
                    'slot_time': f"{slot_start.strftime('%I:%M %p')} - {slot_end.strftime('%I:%M %p')}",
                    'course_name': "-",
                    'batch_id': "-",
                    'current_module': "-",
                    'end_date': "-",
                    'status': 'Available',
                    'availability': slot.get('availability', 'N/A'),
                    'mode': slot.get('mode', 'N/A'),
                    'percentage': 0,
                })
        
        available_count = len(trainer.timing_slots) - occupied_count

        response_data = {
            'availability': availability_data,
            'stats': {
                'total_batches': total_batches,
                'completed_batches': completed_batches,
                'ongoing_batches': ongoing_batches,
                'yts_batches': yts_batches,
                'occupied_count': occupied_count,
                'available_count': available_count,
            }
        }
        return JsonResponse(response_data, safe=False)
        
    except Trainer.DoesNotExist:
        return JsonResponse({'availability': [], 'stats': {}}, safe=False)

from coursedb.models import Course

def trainers_by_course(request):
    course_name = request.GET.get('course_name')
    if not course_name:
        return JsonResponse({'trainers': []})

    try:
        course = Course.objects.get(course_name__iexact=course_name)
        trainers = Trainer.objects.filter(stack=course, is_active=True)
        
        trainers_data = []
        for trainer in trainers:
            active_batches = Batch.objects.filter(trainer=trainer, batch_status__in=['IP', 'YTS'])
            occupied_slots = 0
            if trainer.timing_slots:
                for slot in trainer.timing_slots:
                    slot_start = datetime.strptime(slot['start_time'], "%H:%M").time()
                    slot_end = datetime.strptime(slot['end_time'], "%H:%M").time()
                    if active_batches.filter(start_time=slot_start, end_time=slot_end).exists():
                        occupied_slots += 1
                available_slots_count = len(trainer.timing_slots) - occupied_slots
            else:
                available_slots_count = 0
            
            trainers_data.append({
                'id': trainer.id,
                'name': trainer.name,
                'trainer_id': trainer.trainer_id,
                'timing_slots_count': available_slots_count,
            })
        
        return JsonResponse({'trainers': trainers_data})
    except Course.DoesNotExist:
        return JsonResponse({'trainers': []})

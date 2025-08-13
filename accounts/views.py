from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import CustomUser
from .forms import UserForm, UserUpdateForm, PasswordChangeForm

def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

def is_staff(user):
    return user.is_authenticated and user.role == 'staff'

def is_consultant(user):
    return user.is_authenticated and user.role == 'consultant'

def is_placement(user):
    return user.is_authenticated and user.role == 'placement'

def is_batch_coordinator(user):
    return user.is_authenticated and user.role == 'batch_coordination'
from django.db.models import Sum, Q
from batchdb.models import Batch
from django.db.models.functions import TruncMonth
from studentsdb.models import Student
from paymentdb.models import Payment
from settingsdb.models import TransactionLog
from placementdb.models import Placement
from placementdrive.models import PlacementDrive
from placementdb.models import CompanyInterview
from datetime import datetime

from django.utils import timezone
from datetime import timedelta
from trainersdb.models import Trainer
from django.db.models import Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

@login_required
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

    # Monthly pending amounts
    monthly_pending = (
        Payment.objects
        .annotate(month=TruncMonth('emi_1_date'))
        .values('month')
        .annotate(total=Sum('total_pending_amount'))
        .order_by('month')
    )

    monthly_pending_data = [
        {'month': item['month'].strftime('%Y-%m'), 'amount': float(item['total'])}
        for item in monthly_pending if item['month']
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

                upcoming_payments_list.append({
                    'student_id': payment.student.student_id,
                    'student_name': f"{payment.student.first_name} {payment.student.last_name or ''}",
                    'mobile': payment.student.phone,
                    'course': 'N/A', # Course information is no longer directly accessible
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

    # Monthly pending amounts
    monthly_pending = (
        Payment.objects
        .annotate(month=TruncMonth('emi_1_date'))
        .values('month')
        .annotate(total=Sum('total_pending_amount'))
        .order_by('month')
    )

    monthly_pending_data = [
        {'month': item['month'].strftime('%Y-%m'), 'amount': float(item['total'])}
        for item in monthly_pending if item['month']
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

                upcoming_payments_list.append({
                    'student_id': payment.student.student_id,
                    'student_name': f"{payment.student.first_name} {payment.student.last_name or ''}",
                    'mobile': payment.student.phone,
                    'course': 'N/A', # Course information is no longer directly accessible
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
    consultant = request.user.consultant_profile.consultant
    total_students = Student.objects.filter(consultant=consultant).count()
    goals = consultant.goals.all()
    achievements = consultant.achievements.all()

    context = {
        'total_students': total_students,
        'goals': goals,
        'achievements': achievements,
    }
    return render(request, 'accounts/consultant_dashboard.html', context)

@login_required
@user_passes_test(is_placement)
def placement_dashboard(request):
    # Base Querysets
    students_in_pool = Student.objects.filter(pl_required=True)
    placements = Placement.objects.filter(student__in=students_in_pool)
    drives = PlacementDrive.objects.all()

    # Overall Stats
    total_placement_pool = students_in_pool.count()
    total_placed = students_in_pool.filter(course_status='P').count()
    
    # Actively seeking students for the main stat card
    actively_seeking_stat = placements.filter(is_active=True, student__course_status__in=['IP', 'C', 'YTS']).count()
    
    placement_rate = ((total_placed / total_placement_pool) * 100) if total_placement_pool > 0 else 0
    active_drives_count = drives.count()
    interviews_scheduled = CompanyInterview.objects.count()

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
    recently_placed = students_in_pool.filter(course_status='P').order_by('-end_date')[:5]
    upcoming_interviews = CompanyInterview.objects.filter(interview_date__gte=timezone.now().date()).select_related('placement__student', 'company').order_by('interview_date')[:5]
    students_yet_to_be_placed = placements.filter(is_active=True, student__course_status__in=['IP', 'C', 'YTS', 'H']).select_related('student')[:10]

    context = {
        # Stat Cards
        'total_placement_pool': total_placement_pool,
        'actively_seeking': actively_seeking_stat,
        'total_placed': total_placed,
        'placement_rate': round(placement_rate, 1),
        'active_drives_count': active_drives_count,
        'interviews_scheduled': interviews_scheduled,

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
        'recently_placed': recently_placed,
        'upcoming_interviews': upcoming_interviews,
        'students_yet_to_be_placed': students_yet_to_be_placed,
    }
    return render(request, 'accounts/placement_dashboard.html', context)

@login_required
@user_passes_test(is_batch_coordinator)
def batch_coordination_dashboard(request):
    total_students = Student.objects.count()
    total_batches = Batch.objects.count()
    total_trainers = Trainer.objects.count()

    context = {
        'total_students': total_students,
        'total_batches': total_batches,
        'total_trainers': total_trainers,
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
                login(request, user)
                if user.role == 'admin':
                    return redirect('admin_dashboard')
                elif user.role == 'consultant':
                    return redirect('consultant_dashboard')
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
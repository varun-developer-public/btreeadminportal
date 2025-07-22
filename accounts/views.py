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

from django.db.models import Sum
from django.db.models.functions import TruncMonth
from studentsdb.models import Student
from paymentdb.models import Payment
from settingsdb.models import TransactionLog
from datetime import datetime

from django.utils import timezone
from datetime import timedelta
from trainersdb.models import Trainer
from django.db.models import Count

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

@user_passes_test(is_admin)
def user_list(request):
    users = CustomUser.objects.all().order_by('name')
    return render(request, 'accounts/user_list.html', {'users': users})

@user_passes_test(is_admin)
def create_user(request):
    if request.method == 'POST':
        form = UserForm(request.POST)
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
        else:
            return redirect('login') # Fallback

    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=user_to_update)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully.")
            # Redirect back to the same page to show changes
            return redirect('update_user', pk=pk)
    else:
        form = UserUpdateForm(instance=user_to_update)

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
            else:
                return redirect('staff_dashboard')
    else:
        form = PasswordChangeForm(request.user)
    return render(request, 'accounts/password_change.html', {'form': form})
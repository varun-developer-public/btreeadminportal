from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import CustomUser
from .forms import UserForm, UserUpdateForm

def is_admin(user):
    return user.is_authenticated and user.role == 'admin'

def is_staff(user):
    return user.is_authenticated and user.role == 'staff'

from django.db.models import Sum
from django.db.models.functions import TruncMonth
from studentsdb.models import Student
from paymentdb.models import Payment
from settingsdb.models import TransactionLog
from datetime import datetime

@login_required
def admin_dashboard(request):
    total_students = Student.objects.count()
    total_pending_amount = Payment.objects.aggregate(total_pending=Sum('total_pending_amount'))['total_pending'] or 0

    # Monthly pending amounts
    monthly_pending = (
        Payment.objects
        .annotate(month=TruncMonth('emi_1_date'))
        .values('month')
        .annotate(total=Sum('total_pending_amount'))
        .order_by('month')
    )

    import json
    from django.core.serializers.json import DjangoJSONEncoder

    # Convert month to string for template
    monthly_pending_data = [
        {'month': item['month'].strftime('%Y-%m'), 'total': float(item['total'])}
        for item in monthly_pending if item['month']
    ]

    recent_activities = TransactionLog.objects.order_by('-timestamp')[:10]

    context = {
        'total_students': total_students,
        'total_pending_amount': total_pending_amount,
        'monthly_pending': json.dumps(monthly_pending_data, cls=DjangoJSONEncoder),
        'recent_activities': recent_activities,
    }
    return render(request, 'accounts/admin_dashboard.html', context)

@login_required
def staff_dashboard(request):
    return render(request, 'accounts/staff_dashboard.html')

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

@user_passes_test(is_admin)
def update_user(request, pk):
    user = get_object_or_404(CustomUser, pk=pk)
    if request.method == 'POST':
        form = UserUpdateForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "User updated successfully.")
            return redirect('user_list')
    else:
        form = UserUpdateForm(instance=user)
    return render(request, 'accounts/update_user.html', {'form': form, 'user': user})

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
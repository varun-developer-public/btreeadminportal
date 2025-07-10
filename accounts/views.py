from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required

def login_view(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('admin_dashboard')
        else:
            return redirect('staff_dashboard')

    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)
            if user.is_superuser:
                return redirect('admin_dashboard')
            else:
                return redirect('staff_dashboard')
        else:
            messages.error(request, "Invalid email or password.")

    return render(request, 'accounts/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def admin_dashboard(request):
    if not request.user.is_superuser:
        return redirect('staff_dashboard')  # or raise 403
    return render(request, 'accounts/admin_dashboard.html')

@login_required
def staff_dashboard(request):
    if request.user.is_superuser:
        return redirect('admin_dashboard')  # optional
    return render(request, 'accounts/staff_dashboard.html')
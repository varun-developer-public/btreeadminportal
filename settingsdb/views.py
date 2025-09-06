from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from .models import SourceOfJoining, PaymentAccount, TransactionLog, UserSettings
from .forms import SourceForm, PaymentAccountForm, UserSettingsForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import pandas as pd
from django.http import HttpResponse
from io import BytesIO
import csv

from coursedb.models import Course, CourseCategory
from studentsdb.models import Student
from trainersdb.models import Trainer
from consultantdb.models import Consultant
from batchdb.models import Batch
from paymentdb.models import Payment
from placementdb.models import Placement, CompanyInterview
from placementdrive.models import Company
from accounts.models import CustomUser
import json

import pyotp
import qrcode
import base64


@staff_member_required
def settings_dashboard(request):
    return render(request, 'settingsdb/dashboard.html')

@staff_member_required
def source_list(request):
    sources = SourceOfJoining.objects.all()
    if request.method == 'POST':
        form = SourceForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('source_list')
    else:
        form = SourceForm()
    return render(request, 'settingsdb/source_list.html', {'sources': sources, 'form': form})

@staff_member_required
def remove_source(request, pk):
    source = get_object_or_404(SourceOfJoining, pk=pk)
    source.delete()
    return redirect('source_list')

@staff_member_required
def payment_account_list(request):
    accounts = PaymentAccount.objects.all()
    if request.method == 'POST':
        form = PaymentAccountForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('payment_account_list')
    else:
        form = PaymentAccountForm()
    return render(request, 'settingsdb/payment_account_list.html', {'accounts': accounts, 'form': form})

@staff_member_required
def remove_payment_account(request, pk):
    account = get_object_or_404(PaymentAccount, pk=pk)
    account.delete()
    return redirect('payment_account_list')

def clean_transaction_data(details_json):
    try:
        raw_data = json.loads(details_json)
        cleaned_lines = []
        for field, value in raw_data.items():
            if field == 'csrfmiddlewaretoken':
                continue
            if isinstance(value, list):
                value = value[0]
            cleaned_lines.append(f"{field}: {value}")
        return "\n".join(cleaned_lines)
    except Exception as e:
        return f"Error parsing details: {e}"

@staff_member_required
def transaction_log(request):
    log_list = TransactionLog.objects.select_related('user').order_by('-timestamp')
    
    # Pagination
    paginator = Paginator(log_list, 20)  # Show 20 logs per page
    page = request.GET.get('page')
    try:
        logs = paginator.page(page)
    except PageNotAnInteger:
        logs = paginator.page(1)
    except EmptyPage:
        logs = paginator.page(paginator.num_pages)

    for log in logs:
        log.cleaned_details = clean_transaction_data(log.changes)
        
    return render(request, 'settingsdb/transaction_log.html', {'logs': logs})

@staff_member_required
def export_data(request):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        models_to_export = {
            'Students': Student,
            'Courses': Course,
            'CourseCategories': CourseCategory,
            'Trainers': Trainer,
            'Consultants': Consultant,
            'Batches': Batch,
            'Payments': Payment,
            'Placements': Placement,
            'CompanyInterviews': CompanyInterview,
            'PlacementDrives': Company,
            'Users': CustomUser,
            'SourceOfJoining': SourceOfJoining,
            'PaymentAccounts': PaymentAccount,
        }

        for sheet_name, model in models_to_export.items():
            data = list(model.objects.all().values())
            df = pd.DataFrame(data)
            
            # Convert datetime columns to timezone-unaware
            for col in df.columns:
                if pd.api.types.is_datetime64_any_dtype(df[col]):
                    df[col] = df[col].dt.tz_localize(None)
            
            df.to_excel(writer, sheet_name=sheet_name, index=False)

    output.seek(0)
    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="backup_data.xlsx"'
    return response

from django.db import transaction

@staff_member_required
def import_data(request):
    if request.method == 'POST':
        excel_file = request.FILES['excel_file']
        xls = pd.ExcelFile(excel_file)
        
        with transaction.atomic():
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(xls, sheet_name).replace({pd.NaT: None, float('nan'): None})
                model = None
                if sheet_name == 'Students': model = Student
                elif sheet_name == 'Courses': model = Course
                elif sheet_name == 'CourseCategories': model = CourseCategory
                elif sheet_name == 'Trainers': model = Trainer
                elif sheet_name == 'Consultants': model = Consultant
                elif sheet_name == 'Batches': model = Batch
                elif sheet_name == 'Payments': model = Payment
                elif sheet_name == 'Placements': model = Placement
                elif sheet_name == 'CompanyInterviews': model = CompanyInterview
                elif sheet_name == 'PlacementDrives': model = Company
                elif sheet_name == 'Users': model = CustomUser
                elif sheet_name == 'SourceOfJoining': model = SourceOfJoining
                elif sheet_name == 'PaymentAccounts': model = PaymentAccount

                if model:
                    for _, row in df.iterrows():
                        model.objects.update_or_create(id=row['id'], defaults=row.to_dict())

        return redirect('settings_dashboard')
    return render(request, 'settingsdb/import_data.html')


@staff_member_required
def import_student_courses(request):
    if request.method == 'POST':
        csv_file = request.FILES['csv_file']
        if not csv_file.name.endswith('.csv'):
            return render(request, 'settingsdb/import_courses.html', {'error': 'Please upload a valid CSV file.'})

        try:
            decoded_file = csv_file.read().decode('utf-8').splitlines()
            reader = csv.DictReader(decoded_file)
            errors = []
            
            for row in reader:
                student_id = row.get('student_id')
                course_category_name = row.get('course_category')
                course_name = row.get('course_name')

                if not all([student_id, course_category_name, course_name]):
                    errors.append({**row, 'error': 'Missing required fields.'})
                    continue

                try:
                    student = Student.objects.get(student_id=student_id)
                    category = CourseCategory.objects.get(name=course_category_name)
                    course = Course.objects.get(course_name=course_name, category=category)
                    student.course_id = course.id
                    student.save()
                except Student.DoesNotExist:
                    errors.append({**row, 'error': f'Student with ID {student_id} not found.'})
                except CourseCategory.DoesNotExist:
                    errors.append({**row, 'error': f'Course category "{course_category_name}" not found.'})
                except Course.DoesNotExist:
                    errors.append({**row, 'error': f'Course "{course_name}" in category "{course_category_name}" not found.'})

            if errors:
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = 'attachment; filename="error.csv"'
                writer = csv.writer(response)
                writer.writerow(errors[0].keys())
                for error in errors:
                    writer.writerow(error.values())
                return response

        except Exception as e:
            return render(request, 'settingsdb/import_courses.html', {'error': f'An error occurred: {e}'})

        return redirect('settings_dashboard')

    return render(request, 'settingsdb/import_courses.html')

@staff_member_required
def download_course_template(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="course_template.csv"'
    writer = csv.writer(response)
    writer.writerow(['student_id', 'course_category', 'course_name'])
    return response

@staff_member_required
def export_student_courses(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="student_courses.csv"'

    writer = csv.writer(response)
    writer.writerow(['student_id', 'category_name', 'course_name'])

    students = Student.objects.all().prefetch_related('course__category')

    for student in students:
        if student.course:
            writer.writerow([
                student.student_id,
                student.course.category.name,
                student.course.course_name
            ])
        else:
            writer.writerow([
                student.student_id,
                'N/A',
                'N/A'
            ])

    return response

@login_required
def manage_2fa(request):
    user_settings, created = UserSettings.objects.get_or_create(user=request.user)
    form = UserSettingsForm(instance=user_settings)
    qr_code = None

    if request.method == 'POST':
        form = UserSettingsForm(request.POST, instance=user_settings)
        if form.is_valid():
            user_settings = form.save()
            if user_settings.enable_2fa and not request.user.totp_secret:
                # Generate and save a new TOTP secret
                totp_secret = pyotp.random_base32()
                request.user.totp_secret = totp_secret
                request.user.save()

                # Generate QR code
                totp_uri = pyotp.totp.TOTP(totp_secret).provisioning_uri(
                    name=request.user.email, issuer_name="BTree"
                )
                img = qrcode.make(totp_uri)
                buffered = BytesIO()
                img.save(buffered, format="PNG")
                qr_code = base64.b64encode(buffered.getvalue()).decode()

            elif not user_settings.enable_2fa:
                # Disable 2FA and clear the secret
                request.user.totp_secret = None
                request.user.save()

    context = {
        'form': form,
        'qr_code': qr_code,
        'user_settings': user_settings,
    }
    return render(request, 'settingsdb/manage_2fa.html', context)

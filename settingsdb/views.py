from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import get_object_or_404, render, redirect
from .models import SourceOfJoining, PaymentAccount, TransactionLog, UserSettings, DBBackupImport
from .forms import SourceForm, PaymentAccountForm, UserSettingsForm, DBBackupImportForm
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
import pandas as pd
from django.http import HttpResponse
from io import BytesIO
import csv
from django.db import IntegrityError, models, connections
from django.core.exceptions import ObjectDoesNotExist
from django.apps import apps
from django.contrib import messages
from django.utils import timezone

from coursedb.models import Course, CourseCategory
from studentsdb.models import Student
from trainersdb.models import Trainer
from consultantdb.models import Consultant
from batchdb.models import Batch, BatchStudent
from paymentdb.models import Payment
from placementdb.models import Placement, CompanyInterview
from placementdrive.models import Company
from accounts.models import CustomUser
import json
from django.apps import apps
from batchdb.models import Batch, BatchStudent, BatchTransaction, TrainerHandover, TransferRequest
from consultantdb.models import Consultant, ConsultantProfile, Goal, Achievement
from coursedb.models import Course, CourseCategory, CourseModule, Topic
from paymentdb.models import Payment
from placementdb.models import Placement, CompanyInterview
from placementdrive.models import Company, Interview, InterviewStudent, ResumeSharedStatus
from studentsdb.models import Student
from trainersdb.models import Trainer

import pyotp
import qrcode
import base64

from .db_utils import get_current_db_engine, import_sql_backup
import logging

logger = logging.getLogger(__name__)


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
            sheet_order = [
                'SourceOfJoining', 'PaymentAccounts', 'CourseCategories', 'Courses',
                'Trainers', 'Consultants', 'Users', 'Students', 'Batches',
                'Payments', 'PlacementDrives', 'Placements', 'CompanyInterviews'
            ]
            for sheet_name in sheet_order:
                if sheet_name not in xls.sheet_names:
                    continue
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
                        row_data = row.to_dict()
                        
                        if sheet_name == 'Trainers':
                            for field in ['timing_slots', 'commercials']:
                                if field in row_data and isinstance(row_data[field], str):
                                    try:
                                        row_data[field] = json.loads(row_data[field].replace("'", '"'))
                                    except json.JSONDecodeError:
                                        row_data[field] = []

                        # Handle foreign key relationships
                        for field, value in row_data.items():
                            if isinstance(value, float) and pd.isna(value):
                                row_data[field] = None
                            elif field.endswith('_id') and value is not None:
                                # This is a simplified approach. A more robust solution would map model names to app labels.
                                # For now, we'll assume the related model is in the same app or a known app.
                                pass
                        try:
                            # Separate foreign key fields
                            fk_fields = {}
                            for field in model._meta.fields:
                                if isinstance(field, models.ForeignKey):
                                    fk_fields[field.name + '_id'] = row_data.pop(field.name + '_id', None)

                            # Create or update the object without the foreign keys
                            obj, created = model.objects.update_or_create(id=row_data.pop('id'), defaults=row_data)

                            # Set the foreign keys separately
                            for field, value in fk_fields.items():
                                if value is not None:
                                    setattr(obj, field, value)
                            obj.save()

                        except (IntegrityError, ObjectDoesNotExist) as e:
                            print(f"Error importing row for {sheet_name}: {row_data} - {e}")
                            continue

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
@staff_member_required
def delete_all_data(request):
    models_to_truncate = [
        Payment, CompanyInterview, Placement, BatchStudent, Batch, Student,
        Course, CourseCategory, Trainer, Consultant, CustomUser,
        SourceOfJoining, PaymentAccount, Company
    ]

    if request.method == 'POST':
        for model in models_to_truncate:
            model.objects.all().delete()
        return redirect('settings_dashboard')

    return render(request, 'settingsdb/delete_all_data.html', {
        'models_to_truncate': [model.__name__ for model in models_to_truncate]
    })

@staff_member_required
def settings_view(request):
    return render(request, 'settingsdb/settings.html')


def is_superuser(user):
    return user.is_superuser

@user_passes_test(is_superuser)
def import_db_backup(request):
    # Define the models in the correct order for deletion (reverse dependency order)
    models_to_truncate = [
        # Level 4
        InterviewStudent,
        # Level 3
        BatchStudent, BatchTransaction, TrainerHandover, TransferRequest,
        CompanyInterview, Interview,
        # Level 2
        Batch, CourseModule, Topic, Payment, Placement,
        ResumeSharedStatus, Student,
        # Level 1
        ConsultantProfile, Goal, Achievement, Course,
        UserSettings, DBBackupImport, TransactionLog,
        # Level 0
        CustomUser, Consultant, CourseCategory, SourceOfJoining,
        PaymentAccount, Company, Trainer
    ]
    """
    View for importing database backup (SQL file).
    Only accessible to superusers.
    """
    # Get current database engine
    db_engine = get_current_db_engine()
    db_engine_display = {
        'sqlite': 'SQLite',
        'postgresql': 'PostgreSQL',
        'mysql': 'MySQL',
        'unknown': 'Unknown'
    }.get(db_engine, db_engine.capitalize())
    
    # Get recent imports
    recent_imports = DBBackupImport.objects.order_by('-uploaded_at')[:5]
    
    if request.method == 'POST':
        form = DBBackupImportForm(request.POST, request.FILES)
        if form.is_valid():
            # Create the import record but don't save it yet
            db_import = form.save(commit=False)
            db_import.imported_by = request.user
            db_import.status = 'PROCESSING'
            db_import.save()
            
            # Clear all existing data before import
            try:
                logger.info("Clearing all existing data before database import...")
                for model in models_to_truncate:
                    model.objects.all().delete()
                logger.info("All data cleared successfully.")
            except Exception as e:
                logger.error(f"Error clearing data before import: {str(e)}")
                messages.error(request, f"Error clearing data before import: {str(e)}")
                db_import.status = 'FAILED'
                db_import.error_message = f"Failed to clear old data: {str(e)}"
                db_import.save()
                return redirect('import_db_backup')

            # Process the uploaded file
            try:
                success, message, tables_affected = import_sql_backup(
                    db_import.uploaded_file.path,
                    request.user
                )
                
                # Update the import record
                # Re-fetch the user object in case it was deleted and re-created during import
                try:
                    user = CustomUser.objects.get(id=request.user.id)
                    db_import.imported_by = user
                except CustomUser.DoesNotExist:
                    # If the user was deleted and not restored, set the importer to null
                    db_import.imported_by = None

                db_import.processed_at = timezone.now()
                db_import.status = 'COMPLETED' if success else 'FAILED'
                db_import.error_message = None if success else message
                db_import.db_engine_used = db_engine
                db_import.tables_affected = tables_affected
                db_import.save()
                
                if success:
                    messages.success(request, f"Database backup imported successfully. Affected {len(tables_affected)} tables.")
                else:
                    messages.error(request, f"Error importing database backup: {message}", extra_tags='danger')
                    
            except Exception as e:
                # Handle any unexpected errors
                db_import.processed_at = timezone.now()
                db_import.status = 'FAILED'
                db_import.error_message = str(e)
                db_import.save()
                messages.error(request, f"Unexpected error importing database backup: {str(e)}")
            
            return redirect('import_db_backup')
    else:
        form = DBBackupImportForm()
    
    return render(request, 'settingsdb/import_db_backup.html', {
        'form': form,
        'db_engine': db_engine_display,
        'recent_imports': recent_imports
    })

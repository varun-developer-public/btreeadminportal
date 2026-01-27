from django.shortcuts import render, redirect,get_object_or_404

from consultantdb.models import Consultant
from settingsdb.models import PaymentAccount, SourceOfJoining
from trainersdb.models import Trainer
from .forms import StudentForm, StudentFilterForm
from .models import Student
from coursedb.models import Course, CourseCategory
from paymentdb.models import Payment
from paymentdb.forms import PaymentForm
from placementdb.forms import PlacementUpdateForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Max, Case, When, BooleanField, Value, IntegerField
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .forms import StudentUpdateForm
from dateutil.relativedelta import relativedelta
from placementdb.models import CompanyInterview, Placement

import pandas as pd
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_http_methods
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from .serializers import message_to_dict
from django.db import transaction
from datetime import datetime

@login_required
def student_remarks(request):
    form = StudentFilterForm(request.GET)
    user = request.user
    if hasattr(user, 'consultant_profile'):
        student_qs = Student.objects.filter(consultant=user.consultant_profile.consultant, conversation__isnull=False)
    else:
        student_qs = Student.objects.filter(conversation__isnull=False)
    if form.is_valid():
        query = form.cleaned_data.get('q')
        course_category = form.cleaned_data.get('course_category')
        course = form.cleaned_data.get('course')
        course_status = form.cleaned_data.get('course_status')
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')
        status = form.cleaned_data.get('status')
        payment_status = form.cleaned_data.get('payment_status')
        if status:
            student_qs = student_qs.filter(**{f'{status}': True})
        if query:
            student_qs = student_qs.filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(email__icontains=query) |
                Q(phone__icontains=query) |
                Q(student_id__icontains=query)
            )
        if course:
            student_qs = student_qs.filter(course_id=course.id)
        elif course_category:
            course_ids = Course.objects.filter(category=course_category).values_list('id', flat=True)
            student_qs = student_qs.filter(course_id__in=course_ids)
        if course_status:
            student_qs = student_qs.filter(course_status=course_status)
        if start_date:
            student_qs = student_qs.filter(enrollment_date__gte=start_date)
        if end_date:
            student_qs = student_qs.filter(enrollment_date__lte=end_date)
        if payment_status:
            if payment_status == 'Pending':
                student_qs = student_qs.filter(payment__total_pending_amount__gt=0).distinct()
            elif payment_status == 'Paid':
                student_qs = student_qs.filter(payment__total_pending_amount__lte=0).distinct()
    
    # Priority and Hashtag filters
    priority_filter = request.GET.get('priority')
    hashtag_filter = request.GET.get('hashtag')
    
    if priority_filter:
        priority_map = {'high': 3, 'medium': 2, 'low': 1}
        level = priority_map.get(priority_filter)
        if level:
            student_qs = student_qs.filter(conversation__last_message_priority_level=level)
            
    if hashtag_filter:
        student_qs = student_qs.filter(conversation__last_message_hashtag=hashtag_filter)

    student_qs = student_qs.select_related('conversation').annotate(
        has_unread=Case(
            When(conversation__unread_count__gt=0, then=Value(True)),
            default=Value(False),
            output_field=BooleanField(),
        ),
        effective_priority=Case(
            When(conversation__unread_count__gt=0, then='conversation__priority_level'),
            default=Value(0),
            output_field=IntegerField(),
        )
    ).order_by(
        '-has_unread', 
        '-effective_priority',
        '-conversation__last_message_at',
        '-id'
    )
    paginator = Paginator(student_qs, 10)
    page = request.GET.get('page')
    try:
        students = paginator.page(page)
    except PageNotAnInteger:
        students = paginator.page(1)
    except EmptyPage:
        students = paginator.page(paginator.num_pages)
    selected_id = request.GET.get('sid')
    selected_student = None
    # Removed default selection of first student
    if selected_id:
        try:
            selected_student = Student.objects.get(pk=int(selected_id))
        except (Student.DoesNotExist, ValueError, TypeError):
            selected_student = None
    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']

    # Prepare JSON data for client-side rendering
    students_data = []
    for s in students:
        conv = s.conversation
        students_data.append({
            'id': s.id,
            'first_name': s.first_name,
            'last_name': s.last_name or '',
            'student_id': s.student_id,
            'unread_count': conv.unread_count,
            'is_priority': conv.last_message_priority, # Use the last-message-only derived flag
            'priority_level': conv.last_message_priority_level, # Use the last-message-only derived flag
            'last_message': conv.last_message,
            'last_message_time': conv.last_message_at.isoformat() if conv.last_message_at else None,
        })

    context = {
        'students': students,
        'students_data': students_data,
        'form': form,
        'selected_student': selected_student,
        'selected_id': selected_id,
        'query_params': query_params.urlencode(),
        'selected_priority': priority_filter,
        'selected_hashtag': hashtag_filter,
    }
    return render(request, 'studentsdb/student_remarks.html', context)

@login_required
def create_student(request):
    if request.method == 'POST':
        student_form = StudentForm(request.POST, request=request)
        payment_form = PaymentForm(request.POST, request.FILES)

        if student_form.is_valid() and payment_form.is_valid():
            # Save student first
            student = student_form.save(commit=False)
            
            # Get course_id from the form and assign it to the student
            course = student_form.cleaned_data.get('course')
            if course:
                student.course_id = course.id
            
            student.country_code = request.POST.get('country_code')
            student.alternative_country_code = request.POST.get('alternative_country_code')
            student.save()

            # Create payment object but don't commit yet
            payment = payment_form.save(commit=False)
            payment.student = student
            payment.payment_account = student_form.cleaned_data['payment_account']


            # Calculate pending amount inside Payment model or here
            payment.total_pending_amount = payment.total_fees - payment.amount_paid

            payment.save()

            # Create placement if required
            if student.pl_required:
                Placement.objects.get_or_create(student=student)

            messages.success(request, f"Student {student.student_id} created successfully.", extra_tags='student_message')
            return redirect('student_list')
        else:
            # If forms are not valid, add errors to messages framework
            for field, errors in student_form.errors.items():
                for error in errors:
                    messages.error(request, f"{student_form.fields[field].label}: {error}", extra_tags='student_message')
            for field, errors in payment_form.errors.items():
                for error in errors:
                    messages.error(request, f"{payment_form.fields[field].label}: {error}", extra_tags='student_message')
    else:
        student_form = StudentForm(request=request)
        payment_form = PaymentForm()

    context = {
        'student_form': student_form,
        'payment_form': payment_form,
    }
    return render(request, 'studentsdb/create_student.html', context)
    
    
@login_required
def student_list(request):
    form = StudentFilterForm(request.GET)
    user = request.user
    if hasattr(user, 'consultant_profile'):
        student_list = Student.objects.filter(consultant=user.consultant_profile.consultant).order_by('-id')
    else:
        student_list = Student.objects.prefetch_related('batches', 'batches__trainer').all().order_by('-id')

    if form.is_valid():
        query = form.cleaned_data.get('q')
        course_category = form.cleaned_data.get('course_category')
        course = form.cleaned_data.get('course')
        course_status = form.cleaned_data.get('course_status')
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')
        status = form.cleaned_data.get('status')
        payment_status = form.cleaned_data.get('payment_status')

        if status:
            student_list = student_list.filter(**{f'{status}': True})
        if query:
            student_list = student_list.filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(email__icontains=query) |
                Q(phone__icontains=query) |
                Q(student_id__icontains=query)
            )
        if course:
            student_list = student_list.filter(course_id=course.id)
        elif course_category:
            course_ids = Course.objects.filter(category=course_category).values_list('id', flat=True)
            student_list = student_list.filter(course_id__in=course_ids)
        if course_status:
            student_list = student_list.filter(course_status=course_status)
        if start_date:
            student_list = student_list.filter(enrollment_date__gte=start_date)
        if end_date:
            student_list = student_list.filter(enrollment_date__lte=end_date)
        if payment_status:
            if payment_status == 'Pending':
                student_list = student_list.filter(payment__total_pending_amount__gt=0).distinct()
            elif payment_status == 'Paid':
                student_list = student_list.filter(payment__total_pending_amount__lte=0).distinct()


    for student in student_list:
        batches = student.batches.all()
        unique_trainers = {batch.trainer for batch in batches if batch.trainer}
        unique_batches = {batch for batch in batches}
        student.unique_trainers = list(unique_trainers)
        student.unique_batches = list(unique_batches)
        student.active_batch_ids = list(student.batchstudent_set.filter(is_active=True).values_list('batch_id', flat=True))

    paginator = Paginator(student_list, 10)  # Show 10 students per page
    page = request.GET.get('page')

    try:
        students = paginator.page(page)
    except PageNotAnInteger:
        students = paginator.page(1)
    except EmptyPage:
        students = paginator.page(paginator.num_pages)

    # Get the query parameters
    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']

    return render(request, 'studentsdb/student_list.html', {
        'students': students,
        'form': form,
        'query_params': query_params.urlencode()
    })


@login_required
def update_student(request, student_id):
    student = get_object_or_404(Student.objects.prefetch_related('interview_statuses__interview__company'), student_id=student_id)
    try:
        placement = Placement.objects.get(student=student)
    except Placement.DoesNotExist:
        placement = None

    if request.method == 'POST':
        form = StudentUpdateForm(request.POST, instance=student, user=request.user)
        # Only instantiate placement_form if placement is not None or if pl_required is True
        if placement or form.data.get('pl_required') == 'on':
            if not placement:
                # This is the case where pl_required is newly checked.
                # Create a new placement instance to pass to the form.
                placement = Placement(student=student)
            placement_form = PlacementUpdateForm(request.POST, request.FILES, instance=placement)
        else:
            # If placement is not required and doesn't exist, use a dummy form that won't be saved.
            placement_form = None

        # Debug form validation
        form_valid = form.is_valid()
        placement_form_valid = placement_form.is_valid() if placement_form else True

        if form_valid and placement_form_valid:
            try:
                updated_student = form.save(commit=False)
                
                course = form.cleaned_data.get('course')
                if course:
                    updated_student.course_id = course.id

                if not updated_student.end_date:
                    updated_student.end_date = updated_student.enrollment_date + relativedelta(months=4)

                # Set current user for transaction logging
                from settingsdb.signals import set_current_user
                set_current_user(request.user)
                
                updated_student.save()
                if placement_form and any(field in request.POST for field in placement_form.fields):
                    placement_form.save()
                # === Placement Sync Logic (Only if pl_required changed) ===
                if "pl_required" in form.changed_data:
                    if updated_student.pl_required:
                        placement, created = Placement.objects.get_or_create(student=updated_student)
                        if not created and not placement.is_active:
                            placement.is_active = True
                            placement.save()
                    else:
                        # Instead of delete, just deactivate to preserve history
                        placement = Placement.objects.filter(student=updated_student).first()
                        if placement and placement.is_active:
                            placement.is_active = False
                            placement.save()
            except Exception as e:
                # Debug information
                print(f"Error saving student: {str(e)}")
                messages.error(request, f"Error saving student: {str(e)}", extra_tags='student_message')

            messages.success(request, f"{updated_student.student_id} updated successfully.", extra_tags='student_message')
            return redirect('student_list')
        else:
            # If form is not valid, add errors to messages framework
            print("Form errors:")
            for field, errors in form.errors.items():
                print(f"Field {field}: {errors}")
                for error in errors:
                    # Check if the field has a label before trying to access it
                    label = form.fields[field].label if field in form.fields else field.capitalize()
                    messages.error(request, f"{label}: {error}", extra_tags='student_message')
            if placement_form:
                for field, errors in placement_form.errors.items():
                    print(f"Placement field {field}: {errors}")
                    for error in errors:
                        label = placement_form.fields[field].label if field in placement_form.fields else field.capitalize()
                        messages.error(request, f"{label}: {error}", extra_tags='student_message')
    else:
        form = StudentUpdateForm(instance=student, user=request.user)
        if placement:
            placement_form = PlacementUpdateForm(instance=placement)
        else:
            placement_form = PlacementUpdateForm()

    return render(request, 'studentsdb/update_student.html', {
        'form': form,
        'placement_form': placement_form,
        'student': student
    })


@login_required
def delete_student(request, student_id):
    student = get_object_or_404(Student, student_id=student_id)

    if request.method == 'POST':
        student.delete()
        messages.success(request, f"Student {student.student_id} deleted successfully.", extra_tags='student_message')
        return redirect('student_list')

    return render(request, 'studentsdb/delete_student_confirm.html', {'student': student})


@login_required
def download_student_template(request):
    """
    Downloads an Excel template for bulk student creation.
    """
    data = {
        'student_id': ['BTR0001', 'BTR0002', 'BTR0003', 'BTR0004'],
        'first_name': ['John', 'Jane', '', 'Peter'],
        'last_name': ['Doe', 'Smith', 'Jones', 'Parker'],
        'email': ['john.doe@example.com', 'jane.smith@example.com', 'invalid-email', 'john.doe@example.com'],
        'location': ['CityA', 'CityB', 'CityA', 'CityC'],
        'ugdegree': ['B.Tech', 'B.Sc', 'B.E', 'B.Com'],
        'ugbranch': ['CS', 'IT', 'ECE', 'Accounts'],
        'ugpassout': [2020, 2021, 2020, 2022],
        'ugpercentage': [75.5, 80.0, 65.2, 88.9],
        'pgdegree': ['M.Tech', '', 'MCA', ''],
        'pgbranch': ['CS', '', 'CS', ''],
        'pgpassout': [2022, '', 2022, ''],
        'pgpercentage': [78.0, '', 70.0, ''],
        'working_status': ['NO', 'YES', 'NO', 'YES'],
        'course_status': ['IP', 'YTS', 'C', 'D'],
        'course_id': [1, 2, 3, 4],
        'enrollment_date': ['2025-07-18', '2025-07-19', '2025-07-20', '2025-07-21'],
        'start_date': ['2025-07-20', '2025-07-21', '2025-07-22', '2025-07-23'],
        'end_date': ['2025-11-20', '2025-11-21', '2025-11-22', '2025-11-23'],
        'pl_required': ['Yes', 'No', 'Yes', 'No'],
        'source_of_joining': ['Website', 'Referral', 'Social Media', 'Website'],
        'mode_of_class': ['ON', 'OFF', 'ON', 'ON'],
        'week_type': ['WD', 'WE', 'WD', 'WE'],
        'consultant': ['Consultant A', 'Consultant B', 'Consultant A', ''],
        'trainer': ['Trainer A', 'Trainer B', 'Trainer A', 'Trainer B'],
        'phone': ['1234567890', '0987654321', '1122334455', '5566778899'],
        'payment_account': ['Account 1', 'Account 2', 'Account 1', 'Account 2'],
        'total_fees': [50000, 60000, 70000, 80000],
        'amount_paid': [10000, 20000, 30000, 40000],
        'emi_type': ['2', 'NONE', '3', 'NONE'],
        'emi_1_amount': [20000, '', 15000, ''],
        'emi_1_date': ['2025-08-15', '', '2025-09-01', ''],
        'emi_2_amount': [20000, '', 15000, ''],
        'emi_2_date': ['2025-09-15', '', '2025-10-01', ''],
        'emi_3_amount': ['', '', 10000, ''],
        'emi_3_date': ['', '', '2025-11-01', '']
        # course status - yet to start/ in progress/ completed/refund/discontinued
    }
    df = pd.DataFrame(data)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="student_template.xlsx"'
    df.to_excel(response, index=False)

    return response


@login_required
def import_students(request):
    """
    Imports students from an Excel file.
    """
    if request.method == 'POST':
        excel_file = request.FILES.get('excel_file')
        if not excel_file:
            messages.error(request, "No file was uploaded.", extra_tags='student_message')
            return redirect('student_list')

        try:
            df = pd.read_excel(excel_file)
        except Exception as e:
            messages.error(request, f"Error reading Excel file: {e}", extra_tags='student_message')
            return redirect('student_list')

        required_columns = [
            'student_id', 'first_name', 'last_name', 'email', 'location',
            'ugdegree', 'ugbranch', 'ugpassout', 'ugpercentage',
            'pgdegree', 'pgbranch', 'pgpassout', 'pgpercentage',
            'working_status', 'course_status', 'course_id', 'enrollment_date', 'start_date', 'end_date',
            'pl_required', 'source_of_joining', 'mode_of_class', 'week_type', 'consultant',
            'trainer', 'phone', 'payment_account',
            'total_fees', 'amount_paid', 'emi_type', 'emi_1_amount', 'emi_1_date',
            'emi_2_amount', 'emi_2_date', 'emi_3_amount', 'emi_3_date'
        ]
        if not all(col in df.columns for col in required_columns):
            messages.error(request, f"Excel file must contain the following columns: {', '.join(required_columns)}", extra_tags='student_message')
            return redirect('student_list')

        error_rows = []
        success_count = 0

        for index, row in df.iterrows():
            try:
                with transaction.atomic():
                    student_id = row['student_id']
                    first_name = row['first_name']
                    last_name = row['last_name'] if pd.notna(row['last_name']) else ''
                    email = row.get('email') if pd.notna(row.get('email')) else None
                    total_fees = row['total_fees']
                    amount_paid = row['amount_paid']
                    emi_type = str(row['emi_type'])
                    pl_required = str(row.get('pl_required', '')).lower() == 'yes'
                    source_of_joining_name = row.get('source_of_joining')
                    mode_of_class = row.get('mode_of_class')
                    week_type = row.get('week_type')
                    consultant_name = row.get('consultant')
                    trainer_name = row.get('trainer')
                    course_id = row.get('course_id')
                    phone_val = row.get('phone')
                    if pd.notna(phone_val):
                        phone = str(int(phone_val))
                    else:
                        phone = None
                    payment_account_name = row.get('payment_account')

                    # Validation
                    # Enhanced Validation
                    required_fields = {
                        'student_id': student_id,
                        'first_name': first_name,
                        'total_fees': total_fees,
                        'amount_paid': amount_paid,
                        'mode_of_class': mode_of_class,
                        'week_type': week_type,
                        'payment_account': payment_account_name
                    }

                    missing_fields = []
                    for field, value in required_fields.items():
                        # Check for None, NaN, or empty strings
                        if pd.isna(value) or (isinstance(value, str) and not value.strip()):
                            missing_fields.append(field)
                    
                    if missing_fields:
                        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")

                    if Student.objects.filter(student_id=student_id).exists():
                        raise ValueError("Duplicate student_id.")

                    if email and Student.objects.filter(email=email).exists():
                        raise ValueError("Duplicate email.")

                    # Get or create related objects
                    source_of_joining = None
                    if pd.notna(source_of_joining_name) and str(source_of_joining_name).strip():
                        source_of_joining, _ = SourceOfJoining.objects.get_or_create(name=source_of_joining_name)
                    
                    consultant = None
                    if pd.notna(consultant_name) and consultant_name:
                        consultant, _ = Consultant.objects.get_or_create(name=consultant_name)

                    trainer = None
                    if pd.notna(trainer_name) and str(trainer_name).strip():
                        trainer, _ = Trainer.objects.get_or_create(name=trainer_name)
                    payment_account, _ = PaymentAccount.objects.get_or_create(name=payment_account_name)
                    if not pd.notna(course_id):
                        raise ValueError("course_id is required.")

                    # Clean numeric fields that can be null
                    ugpassout = row.get('ugpassout') if pd.notna(row.get('ugpassout')) else None
                    ugpercentage = row.get('ugpercentage') if pd.notna(row.get('ugpercentage')) else None
                    pgpassout = row.get('pgpassout') if pd.notna(row.get('pgpassout')) else None
                    pgpercentage = row.get('pgpercentage') if pd.notna(row.get('pgpercentage')) else None

                    # Create Student
                    student = Student.objects.create(
                        student_id=student_id,
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        pl_required=pl_required,
                        location=row.get('location') if pd.notna(row.get('location')) else None,
                        ugdegree=row.get('ugdegree') if pd.notna(row.get('ugdegree')) else None,
                        ugbranch=row.get('ugbranch'),
                        ugpassout=ugpassout,
                        ugpercentage=ugpercentage,
                        pgdegree=row.get('pgdegree') if pd.notna(row.get('pgdegree')) else None,
                        pgbranch=row.get('pgbranch'),
                        pgpassout=pgpassout,
                        pgpercentage=pgpercentage,
                        working_status=row.get('working_status') if pd.notna(row.get('working_status')) else 'NO',
                        course_status=row.get('course_status', 'YTS'),
                        course_id=course_id,
                        start_date=row.get('start_date') if pd.notna(row.get('start_date')) else None,
                        end_date=row.get('end_date') if pd.notna(row.get('end_date')) else None,
                        source_of_joining=source_of_joining,
                        mode_of_class=mode_of_class,
                        week_type=week_type,
                        consultant=consultant,
                        trainer=trainer,
                        phone=phone,
                    )

                    if pl_required:
                        Placement.objects.get_or_create(student=student)

                    # Create Payment
                    payment = Payment(
                        student=student,
                        total_fees=total_fees,
                        amount_paid=amount_paid,
                        emi_type=emi_type,
                        payment_account=payment_account
                    )

                    if emi_type != 'NONE':
                        for i in range(1, int(emi_type) + 1):
                            emi_amount = row.get(f'emi_{i}_amount')
                            emi_date_val = row.get(f'emi_{i}_date')
                            
                            if pd.notna(emi_amount) and pd.notna(emi_date_val):
                                emi_date_str = str(emi_date_val).split(' ')[0]
                                try:
                                    emi_date = datetime.strptime(emi_date_str, '%Y-%m-%d').date()
                                    setattr(payment, f'emi_{i}_amount', emi_amount)
                                    setattr(payment, f'emi_{i}_date', emi_date)
                                except (ValueError, TypeError):
                                    raise ValueError(f"Invalid date format for EMI {i} ('{emi_date_str}'). Use YYYY-MM-DD.")
                            elif pd.notna(emi_amount):
                                raise ValueError(f"Missing date for EMI {i}.")
                    
                    payment.save()
                    success_count += 1

            except Exception as e:
                error_row = row.astype(str).to_dict()
                error_row['error_reason'] = str(e)
                error_rows.append(error_row)

        if error_rows:
            request.session['error_rows'] = error_rows
            messages.warning(request, f"Successfully created {success_count} students. {len(error_rows)} records had errors.", extra_tags='student_message')
            return redirect('download_error_report')
        else:
            messages.success(request, f"Successfully created {success_count} students.", extra_tags='student_message')
            return redirect('student_list')

    return render(request, 'studentsdb/import_students.html')


@login_required
def download_error_report(request):
    """
    Downloads a CSV file with the rows that failed during import.
    """
    error_rows = request.session.get('error_rows', [])
    if not error_rows:
        messages.error(request, "No error report to download.", extra_tags='student_message')
        return redirect('student_list')

    df = pd.DataFrame(error_rows)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="error_report.csv"'
    df.to_csv(response, index=False)

    # Clear the session variable
    del request.session['error_rows']

    return response


@login_required
def delete_all_students(request):
    """
    Deletes all students from the database.
    """
    if request.method == 'POST':
        try:
            with transaction.atomic():
                Student.objects.all().delete()
            messages.success(request, "All students have been successfully deleted.", extra_tags='student_message')
        except Exception as e:
            messages.error(request, f"An error occurred while deleting students: {e}", extra_tags='student_message')
    
    return redirect('student_list')

@login_required
def student_report(request, student_id):
    student = get_object_or_404(Student, student_id=student_id)
    interview_statuses = student.interview_statuses.select_related('interview__company').order_by(
        'interview__company__company_name', 'interview__cycle_number', 'interview__round_number'
    )

    interviews_by_company = {}
    for status in interview_statuses:
        company = status.interview.company
        cycle_number = status.interview.cycle_number
        
        if company.company_name not in interviews_by_company:
            interviews_by_company[company.company_name] = {
                'company_obj': company,
                'cycles': {}
            }
        
        if cycle_number not in interviews_by_company[company.company_name]['cycles']:
            interviews_by_company[company.company_name]['cycles'][cycle_number] = []
            
        if status.interview not in interviews_by_company[company.company_name]['cycles'][cycle_number]:
            interviews_by_company[company.company_name]['cycles'][cycle_number].append(status.interview)

    company_interview_data = []
    for company_name, data in interviews_by_company.items():
        earliest_date = None
        for cycle_interviews in data['cycles'].values():
            for interview in cycle_interviews:
                if earliest_date is None or interview.interview_date < earliest_date:
                    earliest_date = interview.interview_date

        total_rounds = sum(len(interviews) for interviews in data['cycles'].values())
        company_interview_data.append({
            'company_name': company_name,
            'company_location': data['company_obj'].get_location_display(),
            'total_cycles': len(data['cycles']),
            'total_rounds': total_rounds,
            'cycles': data['cycles'],
            'earliest_interview_date': earliest_date
        })

    # Sort by most recent first
    company_interview_data.sort(key=lambda x: x['earliest_interview_date'], reverse=True)
    
    # Batch history
    from batchdb.models import BatchStudent
    batch_history = BatchStudent.get_student_batch_history(student)

    # Payment
    try:
        payment = Payment.objects.get(student=student)
    except Payment.DoesNotExist:
        payment = None

    # Placement
    try:
        placement = Placement.objects.get(student=student)
    except Placement.DoesNotExist:
        placement = None

    # ✅ Get selected interview (placed company)
    placed_interview_status = None
    if student.course_status == 'P':
        placed_interview_status = student.interview_statuses.filter(status='placed').select_related('interview__company').first()

    # Latest batch & trainer
    latest_batch = student.batches.order_by('-start_date').first()
    trainer = latest_batch.trainer if latest_batch else None
    from .models import StudentConversation
    conv, _ = StudentConversation.objects.get_or_create(student=student)
    conv_messages = list(conv.messages.select_related('sender').order_by('created_at'))

    context = {
        'student': student,
        'company_interview_data': company_interview_data,
        'batch_history': batch_history,
        'payment': payment,
        'placement': placement,
        'trainer': trainer,
        'placed_interview_status': placed_interview_status,
        'messages': conv_messages,
    }

    return render(request, 'studentsdb/student_report.html', context)

@login_required
@require_http_methods(["GET"])
def conversation_messages(request, student_pk):
    try:
        student = Student.objects.get(pk=int(student_pk))
    except (Student.DoesNotExist, ValueError, TypeError):
        return JsonResponse({"messages": []}, status=404)
    from .models import StudentConversation
    conv, _ = StudentConversation.objects.get_or_create(student=student)
    qs = conv.messages.select_related("sender").order_by("-created_at")[:50]
    data = [message_to_dict(m) for m in reversed(list(qs))]
    return JsonResponse({"messages": data})

def _can_post_http(user):
    if not getattr(user, "is_authenticated", False):
        return False
    return True

@login_required
@require_http_methods(["POST"])
def conversation_send(request, student_pk):
    message_text = str(request.POST.get("message", "")).strip()
    if not message_text:
        return JsonResponse({"ok": False, "reason": "empty"}, status=400)
    if not _can_post_http(request.user):
        return JsonResponse({"ok": False, "reason": "unauthorized"}, status=403)
    
    hashtag = str(request.POST.get("hashtag", "") or "").strip().lower()
    priority = str(request.POST.get("priority", "") or "").strip().lower()
    
    ALLOWED_HASHTAGS = {'placement', 'class', 'payment'}
    ALLOWED_PRIORITIES = {'high', 'medium', 'low'}
    
    if hashtag not in ALLOWED_HASHTAGS:
        hashtag = ""
    if priority not in ALLOWED_PRIORITIES:
        priority = ""

    from .models import StudentConversation, ConversationMessage
    conv, _ = StudentConversation.objects.get_or_create(student_id=student_pk)
    msg = ConversationMessage.objects.create(
        conversation=conv,
        sender=request.user if getattr(request.user, "is_authenticated", False) else None,
        sender_role=getattr(request.user, "role", "") or "",
        message=message_text,
        hashtag=hashtag,
        priority=priority
    )
    try:
        from .models import apply_feedback_from_message
        apply_feedback_from_message(msg, user=request.user)
    except Exception:
        pass

    payload = {"action": "new_message", "message": message_to_dict(msg)}
    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(f"student_{student_pk}", {"type": "broadcast", "payload": payload})
    except Exception:
        pass
    return JsonResponse({"ok": True, "message": message_to_dict(msg)})

@login_required
@require_http_methods(["POST"])
def conversation_upload(request, student_pk):
    if not _can_post_http(request.user):
        return JsonResponse({"ok": False, "reason": "unauthorized"}, status=403)
    
    file_obj = request.FILES.get('file')
    if not file_obj:
        return JsonResponse({"ok": False, "reason": "no file"}, status=400)
    
    # 10MB limit
    if file_obj.size > 10 * 1024 * 1024:
        return JsonResponse({"ok": False, "reason": "file too large (max 10MB)"}, status=400)

    allowed_types = [
        'image/jpeg', 'image/png', 'image/gif', 
        'application/pdf', 
        'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
        'application/vnd.ms-excel', 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        'text/plain'
    ]
    if file_obj.content_type not in allowed_types:
        # Fallback to extension check if content_type is generic or missing
        ext = file_obj.name.split('.')[-1].lower() if '.' in file_obj.name else ''
        allowed_exts = {'jpg', 'jpeg', 'png', 'gif', 'pdf', 'doc', 'docx', 'xls', 'xlsx', 'txt'}
        if ext not in allowed_exts:
             return JsonResponse({"ok": False, "reason": "Unsupported file type"}, status=400)

    from .models import StudentConversation, ConversationMessage
    conv, _ = StudentConversation.objects.get_or_create(student_id=student_pk)
    
    msg_text = request.POST.get('message', '')
    hashtag = request.POST.get('hashtag', '')
    priority = request.POST.get('priority', '')

    msg = ConversationMessage.objects.create(
        conversation=conv,
        sender=request.user,
        sender_role=getattr(request.user, "role", "") or "",
        message_type="file",
        message=msg_text,
        hashtag=hashtag,
        priority=priority,
        file=file_obj,
        file_name=file_obj.name,
        file_size=file_obj.size,
        file_mime=file_obj.content_type
    )

    payload = {"action": "new_message", "message": message_to_dict(msg)}
    try:
        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(f"student_{student_pk}", {"type": "broadcast", "payload": payload})
            
            # Also update remarks list
            remarks_payload = {
                "action": "remarks_list_update",
                "student_id": int(student_pk),
                "message": message_to_dict(msg)
            }
            async_to_sync(channel_layer.group_send)("student_remarks", {"type": "broadcast", "payload": remarks_payload})
    except Exception:
        pass
        
    return JsonResponse(message_to_dict(msg))

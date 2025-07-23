from django.shortcuts import render, redirect,get_object_or_404

from consultantdb.models import Consultant
from settingsdb.models import PaymentAccount, SourceOfJoining
from trainersdb.models import Trainer
from .forms import StudentForm, StudentFilterForm
from .models import Course, Student, CourseCategory
from paymentdb.models import Payment
from paymentdb.forms import PaymentForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .forms import StudentUpdateForm
from dateutil.relativedelta import relativedelta
from placementdb.models import Placement

import pandas as pd
from django.http import HttpResponse
from django.db import transaction
from datetime import datetime

@login_required
def create_student(request):
    if request.method == 'POST':
        student_form = StudentForm(request.POST, request=request)
        payment_form = PaymentForm(request.POST, request.FILES)

        if student_form.is_valid() and payment_form.is_valid():
            # Save student first
            student = student_form.save()

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
        student_list = Student.objects.all().order_by('-id')

    if form.is_valid():
        query = form.cleaned_data.get('q')
        course_category = form.cleaned_data.get('course_category')
        course = form.cleaned_data.get('course')
        course_status = form.cleaned_data.get('course_status')
        working_status = form.cleaned_data.get('working_status')

        if query:
            student_list = student_list.filter(
                Q(first_name__icontains=query) |
                Q(last_name__icontains=query) |
                Q(email__icontains=query) |
                Q(phone__icontains=query)
            )
        if course_category:
            student_list = student_list.filter(course__category=course_category)
        if course:
            student_list = student_list.filter(course=course)
        if course_status:
            student_list = student_list.filter(course_status=course_status)
        if working_status:
            student_list = student_list.filter(working_status=working_status)

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
    student = get_object_or_404(Student, student_id=student_id)

    if request.method == 'POST':
        form = StudentUpdateForm(request.POST, instance=student)
        if form.is_valid():
            updated_student = form.save(commit=False)

            # Auto-set end_date if not already set
            if not updated_student.end_date:
                updated_student.end_date = updated_student.enrollment_date + relativedelta(months=4)

            updated_student.save()

            # === Placement Sync Logic ===
            if updated_student.pl_required:
                # Create if not exists
                Placement.objects.get_or_create(student=updated_student)
            else:
                # Remove placement if exists
                Placement.objects.filter(student=updated_student).delete()

            messages.success(request, f"{updated_student.student_id} updated successfully.", extra_tags='student_message')
            return redirect('student_list')
    else:
        form = StudentUpdateForm(instance=student)

    return render(request, 'studentsdb/update_student.html', {
        'form': form,
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
        'course': ['Python Full Stack', 'Java Full Stack', 'Data Science', 'MERN Stack'],
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
            'working_status', 'course_status', 'course', 'enrollment_date', 'start_date', 'end_date',
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
                    course_name = row.get('course')
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
                    course = None
                    if pd.notna(course_name) and str(course_name).strip():
                        default_category, _ = CourseCategory.objects.get_or_create(name='Default Category')
                        import uuid
                        unique_code = uuid.uuid4().hex[:10].upper()

                        course_name_str = str(course_name).strip()
                        course = Course.objects.filter(name=course_name_str).first()
                        if not course:
                            course = Course.objects.create(
                                name=course_name_str,
                                category=default_category,
                                code=unique_code
                            )

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
                        course=course,
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


from django.http import JsonResponse

def get_courses(request):
    category_id = request.GET.get('category_id')
    courses = Course.objects.filter(category_id=category_id).order_by('name')
    return JsonResponse(list(courses.values('id', 'name')), safe=False)

from django.shortcuts import render, redirect,get_object_or_404

from consultantdb.models import Consultant
from settingsdb.models import PaymentAccount, SourceOfJoining
from trainersdb.models import Trainer
from .forms import StudentForm
from .models import Student
from paymentdb.models import Payment
from paymentdb.forms import PaymentForm
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
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
        student_form = StudentForm(request.POST)
        payment_form = PaymentForm(request.POST, request.FILES) 

        if student_form.is_valid() and payment_form.is_valid():
            # Save student first
            student = student_form.save()

            # Create payment object but don't commit yet
            payment = payment_form.save(commit=False)
            payment.student = student

            # Calculate pending amount inside Payment model or here
            payment.total_pending_amount = payment.total_fees - payment.amount_paid

            payment.save()

            # Create placement if required
            if student.pl_required:
                Placement.objects.get_or_create(student=student)

            messages.success(request, f"Student {student.student_id} created successfully.")
            return redirect('student_list')
    else:
        student_form = StudentForm()
        payment_form = PaymentForm()

    context = {
        'student_form': student_form,
        'payment_form': payment_form,
    }
    return render(request, 'studentsdb/create_student.html', context)
    
    
@login_required
def student_list(request):
    query = request.GET.get('q')
    students = Student.objects.all().order_by('-id')

    if query:
        students = students.filter(
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone__icontains=query)
        )

    return render(request, 'studentsdb/student_list.html', {'students': students, 'query': query})


@login_required
def update_student(request, student_id):
    student = get_object_or_404(Student, student_id=student_id)

    if request.method == 'POST':
        form = StudentUpdateForm(request.POST, instance=student)
        if form.is_valid():
            updated_student = form.save(commit=False)

            # Auto-set tentative_end_date if not already set
            if not updated_student.tentative_end_date:
                updated_student.tentative_end_date = updated_student.join_date + relativedelta(months=4)

            updated_student.save()

            # === Placement Sync Logic ===
            if updated_student.pl_required:
                # Create if not exists
                Placement.objects.get_or_create(student=updated_student)
            else:
                # Remove placement if exists
                Placement.objects.filter(student=updated_student).delete()

            messages.success(request, f"{updated_student.student_id} updated successfully.")
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
        messages.success(request, f"Student {student.student_id} deleted successfully.")
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
        'date_of_birth': ['1999-01-15', '2000-05-20', '2001-02-28', '2000-11-10'],
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
            messages.error(request, "No file was uploaded.")
            return redirect('student_list')

        try:
            df = pd.read_excel(excel_file)
        except Exception as e:
            messages.error(request, f"Error reading Excel file: {e}")
            return redirect('student_list')

        required_columns = [
            'student_id', 'first_name', 'last_name', 'email', 'date_of_birth',
            'pl_required', 'source_of_joining', 'mode_of_class', 'week_type', 'consultant',
            'trainer', 'phone', 'payment_account',
            'total_fees', 'amount_paid', 'emi_type', 'emi_1_amount', 'emi_1_date',
            'emi_2_amount', 'emi_2_date', 'emi_3_amount', 'emi_3_date'
        ]
        if not all(col in df.columns for col in required_columns):
            messages.error(request, f"Excel file must contain the following columns: {', '.join(required_columns)}")
            return redirect('student_list')

        error_rows = []
        success_count = 0

        with transaction.atomic():
            for index, row in df.iterrows():
                try:
                    student_id = row['student_id']
                    first_name = row['first_name']
                    last_name = row['last_name']
                    email = row['email']
                    dob_str = str(row['date_of_birth']).split(' ')[0]
                    total_fees = row['total_fees']
                    amount_paid = row['amount_paid']
                    emi_type = str(row['emi_type'])
                    pl_required = row.get('pl_required', '').lower() == 'yes'
                    source_of_joining_name = row.get('source_of_joining')
                    mode_of_class = row.get('mode_of_class')
                    week_type = row.get('week_type')
                    consultant_name = row.get('consultant')
                    trainer_name = row.get('trainer')
                    phone = row.get('phone')
                    payment_account_name = row.get('payment_account')

                    # Validation
                    if not all([student_id, first_name, last_name, email, dob_str, total_fees, amount_paid, source_of_joining_name, mode_of_class, week_type, trainer_name, phone, payment_account_name]):
                        raise ValueError("Missing required student or payment fields.")

                    try:
                        date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date()
                    except ValueError:
                        raise ValueError("Invalid date_of_birth format. Use YYYY-MM-DD.")

                    if Student.objects.filter(student_id=student_id).exists():
                        raise ValueError("Duplicate student_id.")

                    if Student.objects.filter(email=email).exists():
                        raise ValueError("Duplicate email.")

                    # Get or create related objects
                    source_of_joining, _ = SourceOfJoining.objects.get_or_create(name=source_of_joining_name)
                    consultant = None
                    if consultant_name:
                        consultant, _ = Consultant.objects.get_or_create(name=consultant_name)
                    trainer, _ = Trainer.objects.get_or_create(name=trainer_name)
                    payment_account, _ = PaymentAccount.objects.get_or_create(name=payment_account_name)

                    # Create Student
                    student = Student.objects.create(
                        student_id=student_id,
                        first_name=first_name,
                        last_name=last_name,
                        email=email,
                        date_of_birth=date_of_birth,
                        pl_required=pl_required,
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
                            emi_date_str = str(row.get(f'emi_{i}_date')).split(' ')[0]

                            if emi_amount and emi_date_str:
                                try:
                                    emi_date = datetime.strptime(emi_date_str, '%Y-%m-%d').date()
                                    setattr(payment, f'emi_{i}_amount', emi_amount)
                                    setattr(payment, f'emi_{i}_date', emi_date)
                                except (ValueError, TypeError):
                                     raise ValueError(f"Invalid date format for EMI {i}. Use YYYY-MM-DD.")
                            else:
                                raise ValueError(f"Missing amount or date for EMI {i}.")
                    
                    payment.save()
                    success_count += 1

                except Exception as e:
                    error_row = row.to_dict()
                    error_row['error_reason'] = str(e)
                    error_rows.append(error_row)

        if error_rows:
            request.session['error_rows'] = error_rows
            messages.warning(request, f"Successfully created {success_count} students. {len(error_rows)} records had errors.")
            return redirect('download_error_report')
        else:
            messages.success(request, f"Successfully created {success_count} students.")
            return redirect('student_list')

    return redirect('student_list')


@login_required
def download_error_report(request):
    """
    Downloads a CSV file with the rows that failed during import.
    """
    error_rows = request.session.get('error_rows', [])
    if not error_rows:
        messages.error(request, "No error report to download.")
        return redirect('student_list')

    df = pd.DataFrame(error_rows)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="error_report.csv"'
    df.to_csv(response, index=False)

    # Clear the session variable
    del request.session['error_rows']

    return response

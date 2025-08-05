from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import BatchCreationForm
from .models import Batch
from placementdb.models import Placement
from django.contrib.auth.decorators import login_required
from django.utils import timezone
import pandas as pd
from django.http import HttpResponse
from django.db import transaction
from datetime import datetime
from dateutil.relativedelta import relativedelta
from studentsdb.models import Student
from trainersdb.models import Trainer
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def get_next_batch_id():
    last_batch = Batch.objects.order_by('-id').first()
    if last_batch and last_batch.batch_id.startswith('BAT_'):
        last_num = int(last_batch.batch_id.replace('BAT_', ''))
        return f"BAT_{last_num + 1:03d}"
    return "BAT_001"

def batch_list(request):
    query = request.GET.get('q')
    batch_list = Batch.objects.all().order_by('-id')

    if query:
        batch_list = batch_list.filter(
            Q(batch_name__icontains=query) |
            Q(trainer__name__icontains=query) |
            Q(students__student_id__icontains=query)
        ).distinct()

    paginator = Paginator(batch_list, 10)  # Show 10 batches per page
    page = request.GET.get('page')

    try:
        batches = paginator.page(page)
    except PageNotAnInteger:
        batches = paginator.page(1)
    except EmptyPage:
        batches = paginator.page(paginator.num_pages)

    return render(request, 'batchdb/batch_list.html', {'batches': batches, 'query': query})


def create_batch(request):
    next_batch_id = get_next_batch_id()
    if request.method == 'POST':
        form = BatchCreationForm(request.POST)
        if form.is_valid():
            batch = form.save(commit=False)
            batch.batch_id = next_batch_id # Assign the pre-fetched ID
            
            # Handle custom time slot
            if form.cleaned_data['time_slot'] == 'custom':
                batch.time_slot = form.cleaned_data['custom_time_slot']
            else:
                batch.time_slot = form.cleaned_data['time_slot']

            batch.save()
            form.save_m2m()  # Save ManyToMany relationships

            messages.success(request, "Batch created successfully.")
            return redirect('batch_list')
    else:
        today = timezone.now().date()
        end_date = today + relativedelta(months=2)
        form = BatchCreationForm(initial={
            'batch_id': next_batch_id,
            'start_date': today,
            'end_date': end_date
        })

    return render(request, 'batchdb/create_batch.html', {'form': form, 'next_batch_id': next_batch_id})


def update_batch(request, pk):
    batch = get_object_or_404(Batch, pk=pk)

    if request.method == 'POST':
        form = BatchCreationForm(request.POST, instance=batch)
        if form.is_valid():
            batch = form.save(commit=False)
            selected_students = form.cleaned_data['students']

            batch.save()
            # Replace the batch's students with the updated selection
            batch.students.set(selected_students)

            # Sync Placement DB for all currently assigned students who require placement
            for student in selected_students:
                if student.pl_required:
                    Placement.objects.get_or_create(student=student)

            messages.success(request, f"Batch {batch.batch_id} updated and students synced.")
            return redirect('batch_list')
    else:
        form = BatchCreationForm(instance=batch)

    return render(request, 'batchdb/update_batch.html', {'form': form, 'batch': batch})



def delete_batch(request, pk):
    batch = get_object_or_404(Batch, pk=pk)
    if request.method == 'POST':
        batch.delete()
        messages.success(request, "Batch deleted.")
        return redirect('batch_list')
    return render(request, 'batchdb/delete_confirm.html', {'batch': batch})

@login_required
def download_batch_template(request):
    """
    Downloads an Excel template for bulk batch creation.
    """
    data = {
        'batch_id': ['BAT_101', ''],  # Optional: Leave empty to auto-generate
        'module_name': ['Python', 'Java'],
        'batch_type': ['Weekday', 'Weekend'],
        'trainer': ['Trainer A', 'Trainer B'],
        'start_date': ['2025-08-01', '2025-08-01'],
        'end_date': ['2025-10-01', '2025-10-01'],
        'time_slot': ['9:00 AM - 10:30 AM', '7:00 PM - 8:30 PM'],
        'students': ['BTR0001,BTR0002', 'BTR0003,BTR0004']
    }
    df = pd.DataFrame(data)

    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="batch_template.xlsx"'
    df.to_excel(response, index=False)

    return response

@login_required
def import_batches(request):
    """
    Imports batches from an Excel file.
    """
    if request.method == 'POST':
        excel_file = request.FILES.get('excel_file')
        if not excel_file:
            messages.error(request, "No file was uploaded.")
            return redirect('batch_list')

        try:
            df = pd.read_excel(excel_file)
        except Exception as e:
            messages.error(request, f"Error reading Excel file: {e}")
            return redirect('batch_list')

        required_columns = [
            'module_name', 'batch_type', 'trainer', 'start_date', 'end_date', 'time_slot', 'students'
        ]
        if not all(col in df.columns for col in required_columns):
            messages.error(request, f"Excel file must contain the following columns: {', '.join(required_columns)}")
            return redirect('batch_list')

        error_rows = []
        success_count = 0

        with transaction.atomic():
            for index, row in df.iterrows():
                try:
                    module_name = row['module_name']
                    batch_type = row['batch_type']
                    trainer_name = row['trainer']
                    start_date_str = str(row['start_date']).split(' ')[0]
                    end_date_str = str(row['end_date']).split(' ')[0]
                    time_slot = row['time_slot']
                    student_ids_str = row['students']

                    if not all([module_name, batch_type, trainer_name, start_date_str, end_date_str, time_slot, student_ids_str]):
                        raise ValueError("All fields are mandatory.")
                    
                    student_ids = str(student_ids_str).split(',')

                    try:
                        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
                        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
                    except ValueError:
                        raise ValueError("Invalid date format. Use YYYY-MM-DD.")

                    trainer, _ = Trainer.objects.get_or_create(name=trainer_name)
                    
                    # Handle optional batch_id
                    batch_id_from_sheet = row.get('batch_id')
                    if pd.notna(batch_id_from_sheet) and str(batch_id_from_sheet).strip():
                        batch_id = str(batch_id_from_sheet).strip()
                        if Batch.objects.filter(batch_id=batch_id).exists():
                            raise ValueError(f"Batch with ID '{batch_id}' already exists.")
                        batch = Batch(batch_id=batch_id)
                    else:
                        # Let the model's save() method generate the ID
                        batch = Batch()

                    batch.module_name = module_name
                    batch.batch_type = batch_type
                    batch.trainer = trainer
                    batch.start_date = start_date
                    batch.end_date = end_date
                    batch.time_slot = time_slot
                    batch.save()

                    students = []
                    for student_id in student_ids:
                        student_id = student_id.strip()
                        try:
                            student = Student.objects.get(student_id=student_id)
                            students.append(student)
                        except Student.DoesNotExist:
                            raise ValueError(f"Student with ID {student_id} not found.")
                    
                    batch.students.set(students)

                    for student in students:
                        if student.pl_required:
                            Placement.objects.get_or_create(student=student)

                    success_count += 1

                except Exception as e:
                    error_row = row.to_dict()
                    error_row['error_reason'] = str(e)
                    error_rows.append(error_row)

        if error_rows:
            request.session['error_rows_batch'] = error_rows
            messages.warning(request, f"Successfully created {success_count} batches. {len(error_rows)} records had errors.")
            return redirect('download_error_report_batch')
        else:
            messages.success(request, f"Successfully created {success_count} batches.")
            return redirect('batch_list')

    return render(request, 'batchdb/import_batches.html')

@login_required
def download_error_report_batch(request):
    """
    Downloads a CSV file with the rows that failed during batch import.
    """
    error_rows = request.session.get('error_rows_batch', [])
    if not error_rows:
        messages.error(request, "No error report to download.")
        return redirect('batch_list')

    df = pd.DataFrame(error_rows)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="batch_error_report.csv"'
    df.to_csv(response, index=False)

    del request.session['error_rows_batch']

    return response

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from datetime import datetime
import json
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from .forms import BatchCreationForm, BatchUpdateForm, BatchFilterForm
from .models import Batch
from coursedb.models import Course, CourseCategory
from trainersdb.models import Trainer
from studentsdb.models import Student

def batch_list(request):
    batch_list = Batch.objects.all().order_by('-id')
    form = BatchFilterForm(request.GET)

    if form.is_valid():
        query = form.cleaned_data.get('q')
        courses = form.cleaned_data.get('course')
        trainers = form.cleaned_data.get('trainer')
        statuses = form.cleaned_data.get('batch_status')

        if query:
            batch_list = batch_list.filter(
                Q(students__first_name__icontains=query) |
                Q(students__last_name__icontains=query) |
                Q(batch_id__icontains=query) |
                Q(course__course_name__icontains=query) |
                Q(trainer__name__icontains=query)
            ).distinct()
        
        if courses:
            batch_list = batch_list.filter(course__in=courses).distinct()
        
        if trainers:
            batch_list = batch_list.filter(trainer__in=trainers).distinct()

        if statuses:
            batch_list = batch_list.filter(batch_status__in=statuses).distinct()

    paginator = Paginator(batch_list, 10)
    page = request.GET.get('page')

    try:
        batches = paginator.page(page)
    except PageNotAnInteger:
        batches = paginator.page(1)
    except EmptyPage:
        batches = paginator.page(paginator.num_pages)

    return render(request, 'batchdb/batch_list.html', {
        'batches': batches,
        'form': form
    })

@login_required
def create_batch(request):
    if request.method == 'POST':
        form = BatchCreationForm(request.POST)
        if form.is_valid():
            batch = form.save(commit=False)
            
            time_slot = form.cleaned_data.get('time_slot')
            if time_slot:
                batch.start_time, batch.end_time = time_slot

            days = form.cleaned_data.get('days')
            
            if not days:
                if batch.batch_type == 'WD':
                    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
                elif batch.batch_type == 'WE':
                    days = ['Saturday', 'Sunday']
                elif batch.batch_type == 'WDWE':
                    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            
            batch.days = days
            batch.batch_status = 'YTS'  # Set default status
            batch.created_by = request.user
            batch.save()
            form.save_m2m()
            messages.success(request, "Batch created successfully.")
            return redirect('batch_list')
    else:
        form = BatchCreationForm()
    return render(request, 'batchdb/create_batch.html', {'form': form})

@login_required
def update_batch(request, pk):
    batch = get_object_or_404(Batch, pk=pk)
    if request.method == 'POST':
        form = BatchUpdateForm(request.POST, instance=batch)
        if form.is_valid():
            batch = form.save(commit=False)

            time_slot = form.cleaned_data.get('time_slot')
            if time_slot:
                batch.start_time, batch.end_time = time_slot

            days = form.cleaned_data.get('days')

            if not days:
                if batch.batch_type == 'WD':
                    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
                elif batch.batch_type == 'WE':
                    days = ['Saturday', 'Sunday']
                elif batch.batch_type == 'WDWE':
                    days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']

            batch.days = days
            batch.updated_by = request.user
            batch.save()
            form.save_m2m()
            messages.success(request, f"Batch {batch.batch_id} updated successfully.")
            return redirect('batch_list')
    else:
        form = BatchUpdateForm(instance=batch, initial={'days': batch.days})
    context = {
        'form': form,
        'batch': batch,
    }
    return render(request, 'batchdb/update_batch.html', context)

@login_required
def delete_batch(request, pk):
    batch = get_object_or_404(Batch, pk=pk)
    if request.method == 'POST':
        batch.delete()
        messages.success(request, "Batch deleted successfully.")
        return redirect('batch_list')
    return render(request, 'batchdb/delete_confirm.html', {'batch': batch})

# AJAX Views
@login_required
def get_courses_by_category(request):
    category_id = request.GET.get('category_id')
    courses = Course.objects.filter(category_id=category_id).values('id', 'course_name')
    return JsonResponse(list(courses), safe=False)

@login_required
def get_trainers_for_course(request):
    course_id = request.GET.get('course_id')
    trainers = Trainer.objects.filter(stack__id=course_id).values('id', 'name')
    return JsonResponse(list(trainers), safe=False)

@login_required
def get_trainer_slots(request):
    trainer_id = request.GET.get('trainer_id')
    try:
        trainer = Trainer.objects.get(id=trainer_id)
        active_batches = Batch.objects.filter(trainer=trainer, batch_status__in=['IP', 'YTS'])
        taken_slots = [(batch.start_time, batch.end_time) for batch in active_batches]

        if not isinstance(trainer.timing_slots, list):
            return JsonResponse([], safe=False)

        available_slots = [
            slot for slot in trainer.timing_slots
            if isinstance(slot, dict) and
                (datetime.strptime(slot['start_time'], '%H:%M').time(), datetime.strptime(slot['end_time'], '%H:%M').time()) not in taken_slots
        ]
        
        formatted_slots = []
        for slot in available_slots:
            start_time = slot.get('start_time', '')
            end_time = slot.get('end_time', '')
            name = f"{datetime.strptime(start_time, '%H:%M').strftime('%I:%M %p')} - {datetime.strptime(end_time, '%H:%M').strftime('%I:%M %p')}"
            formatted_slots.append({'id': f"{start_time}-{end_time}", 'name': name})

        return JsonResponse(formatted_slots, safe=False)
    except Trainer.DoesNotExist:
        return JsonResponse([], safe=False)

@login_required
def get_students_for_course(request):
    course_id = request.GET.get('course_id')
    students = Student.objects.filter(
        course_id=course_id,
        course_status__in=['YTS', 'IP']
    ).values('id', 'first_name', 'last_name')
    return JsonResponse(list(students), safe=False)

import pandas as pd
from django.http import HttpResponse
from django.db import transaction
from placementdb.models import Placement

@login_required
def download_batch_template(request):
    data = {
        'batch_id': ['BAT_101', ''],
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
    if request.method == 'POST':
        excel_file = request.FILES.get('excel_file')
        if not excel_file:
            messages.error(request, "No batch file was uploaded.")
            return redirect('batch_list')

        try:
            df = pd.read_excel(excel_file)
        except Exception as e:
            messages.error(request, f"Error reading batch Excel file: {e}")
            return redirect('batch_list')

        required_columns = [
            'module_name', 'batch_type', 'trainer', 'start_date', 'end_date', 'time_slot', 'students'
        ]
        if not all(col in df.columns for col in required_columns):
            messages.error(request, f"Batch Excel file must contain the following columns: {', '.join(required_columns)}")
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
                    
                    batch_id_from_sheet = row.get('batch_id')
                    if pd.notna(batch_id_from_sheet) and str(batch_id_from_sheet).strip():
                        batch_id = str(batch_id_from_sheet).strip()
                        if Batch.objects.filter(batch_id=batch_id).exists():
                            raise ValueError(f"Batch with ID '{batch_id}' already exists.")
                        batch = Batch(batch_id=batch_id)
                    else:
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

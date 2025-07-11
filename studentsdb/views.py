from django.shortcuts import render, redirect,get_object_or_404
from .forms import StudentForm
from .models import Student
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .forms import StudentUpdateForm
from dateutil.relativedelta import relativedelta
from placementdb.models import Placement


@login_required
def create_student(request):
    if request.method == 'POST':
        form = StudentForm(request.POST)
        if form.is_valid():
            student = form.save(commit=False)

            # Auto-calculate pending amount
            student.total_pending_amount = student.total_fees - student.amount_paid

            # Auto-generate student_id handled in model save()
            student.save()

            # === Create Placement if needed ===
            if student.pl_required:
                Placement.objects.get_or_create(student=student)

            messages.success(request, f"Student {student.student_id} created successfully.")
            return redirect('student_list')
    else:
        form = StudentForm()

    return render(request, 'studentsdb/create_student.html', {'form': form})


@login_required
def student_list(request):
    query = request.GET.get('q')
    students = Student.objects.all().order_by('-id')

    if query:
        students = students.filter(
            Q(name__icontains=query) |
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

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import BatchForm
from .models import Batch
from placementdb.models import Placement

def get_next_batch_id():
    last_batch = Batch.objects.order_by('-id').first()
    if last_batch and last_batch.batch_id.startswith('BAT_'):
        last_num = int(last_batch.batch_id.replace('BAT_', ''))
        return f"BAT_{last_num + 1:03d}"
    return "BAT_001"

def batch_list(request):
    batches = Batch.objects.all()
    return render(request, 'batchdb/batch_list.html', {'batches': batches})


def create_batch(request):
    next_batch_id = get_next_batch_id()

    if request.method == 'POST':
        form = BatchForm(request.POST)
        if form.is_valid():
            batch = form.save(commit=False)
            batch.batch_id = next_batch_id  # Set manually
            batch.save()

            batch.students.set(form.cleaned_data['students'])

            # Placement sync
            for student in form.cleaned_data['students']:
                if student.pl_required:
                    Placement.objects.get_or_create(student=student)

            messages.success(request, f"Batch {batch.batch_id} created successfully.")
            return redirect('batch_list')
    else:
        form = BatchForm()

    return render(request, 'batchdb/create_batch.html', {'form': form, 'next_batch_id': next_batch_id})


def update_batch(request, pk):
    batch = get_object_or_404(Batch, pk=pk)

    if request.method == 'POST':
        form = BatchForm(request.POST, instance=batch)
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
        form = BatchForm(instance=batch)

    return render(request, 'batchdb/update_batch.html', {'form': form, 'batch': batch})



def delete_batch(request, pk):
    batch = get_object_or_404(Batch, pk=pk)
    if request.method == 'POST':
        batch.delete()
        messages.success(request, "Batch deleted.")
        return redirect('batch_list')
    return render(request, 'batchdb/delete_confirm.html', {'batch': batch})

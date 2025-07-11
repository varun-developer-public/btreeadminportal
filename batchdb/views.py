from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .forms import BatchForm
from .models import Batch
from placementdb.models import Placement

def batch_list(request):
    batches = Batch.objects.all()
    return render(request, 'batchdb/batch_list.html', {'batches': batches})


def create_batch(request):
    if request.method == 'POST':
        form = BatchForm(request.POST)
        if form.is_valid():
            batch = form.save(commit=False)
            selected_students = form.cleaned_data['students']
            batch.save()  # Save batch first to get a PK

            # Assign students via ManyToMany relation
            batch.students.set(selected_students)

            # Sync Placement DB for students who require placement
            for student in selected_students:
                if student.pl_required:
                    Placement.objects.get_or_create(student=student)

            messages.success(request, f"Batch {batch.batch_id} created and students added.")
            return redirect('batch_list')
    else:
        form = BatchForm()

    return render(request, 'batchdb/create_batch.html', {'form': form})

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

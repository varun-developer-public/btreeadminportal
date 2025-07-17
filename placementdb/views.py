from .models import Placement
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import PlacementUpdateForm
from django.db.models import Q

@login_required
def placement_list(request):
    placements = Placement.objects.select_related('student').all()
    
    search = request.GET.get('search', '').strip()
    student_id = request.GET.get('student_id', '').strip()
    batch_id = request.GET.get('batch_id', '').strip()
    trainer_id = request.GET.get('trainer_id', '').strip()

    if search:
        placements = placements.filter(
            Q(student__first_name__icontains=search) |
            Q(student__last_name__icontains=search) |
            Q(student__student_id__icontains=search)
        )
    
    if student_id:
        placements = placements.filter(student__student_id__icontains=student_id)
    
    if batch_id:
        placements = placements.filter(student__batches__batch_id__icontains=batch_id)
        
    if trainer_id:
        placements = placements.filter(student__batches__trainer__id__icontains=trainer_id)

    return render(request, 'placementdb/placement_list.html', {
        'placements': placements,
        'search': search,
        'student_id': student_id,
        'batch_id': batch_id,
        'trainer_id': trainer_id,
    })

@login_required
def update_placement(request, pk):
    placement = get_object_or_404(Placement, pk=pk)

    if request.method == 'POST':
        form = PlacementUpdateForm(request.POST, instance=placement)
        if form.is_valid():
            form.save()
            messages.success(request, "Placement updated successfully.")
            return redirect('placement_list')
    else:
        form = PlacementUpdateForm(instance=placement)

    return render(request, 'placementdb/update_placement.html', {
        'form': form,
        'placement': placement,
    })

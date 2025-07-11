from .models import Placement
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import PlacementUpdateForm

@login_required
def placement_list(request):
    placements = Placement.objects.select_related('student').all()
    return render(request, 'placementdb/placement_list.html', {
        'placements': placements
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

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import PlacementDrive
from .forms import PlacementDriveForm

@login_required
def placement_drive_list(request):
    drives = PlacementDrive.objects.all()
    return render(request, 'placementdrive/placementdrive_list.html', {'drives': drives})

@login_required
def placement_drive_create(request):
    if request.method == 'POST':
        form = PlacementDriveForm(request.POST)
        if form.is_valid():
            drive = form.save(commit=False)
            drive.created_by = request.user
            drive.save()
            return redirect('placementdrive:drive_list')
    else:
        form = PlacementDriveForm()
    return render(request, 'placementdrive/placementdrive_form.html', {'form': form})

@login_required
def placement_drive_update(request, pk):
    drive = get_object_or_404(PlacementDrive, pk=pk)
    if request.method == 'POST':
        form = PlacementDriveForm(request.POST, instance=drive)
        if form.is_valid():
            form.save()
            return redirect('placementdrive:drive_list')
    else:
        form = PlacementDriveForm(instance=drive)
    return render(request, 'placementdrive/placementdrive_form.html', {'form': form})

@login_required
def placement_drive_delete(request, pk):
    drive = get_object_or_404(PlacementDrive, pk=pk)
    if request.method == 'POST':
        drive.delete()
        return redirect('placementdrive:drive_list')
    return render(request, 'placementdrive/placementdrive_confirm_delete.html', {'drive': drive})
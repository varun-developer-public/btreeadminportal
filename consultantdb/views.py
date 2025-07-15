from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Consultant
from .forms import ConsultantForm

def consultant_list(request):
    consultants = Consultant.objects.all()
    return render(request, 'consultantdb/consultant_list.html', {'consultants': consultants})

def create_consultant(request):
    if request.method == 'POST':
        form = ConsultantForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Consultant added successfully!")
            return redirect('consultant_list')
    else:
        form = ConsultantForm()
    return render(request, 'consultantdb/consultant_form.html', {'form': form, 'title': 'Add Consultant'})

def update_consultant(request, pk):
    consultant = get_object_or_404(Consultant, pk=pk)
    if request.method == 'POST':
        form = ConsultantForm(request.POST, instance=consultant)
        if form.is_valid():
            form.save()
            messages.success(request, "Consultant updated successfully!")
            return redirect('consultant_list')
    else:
        form = ConsultantForm(instance=consultant)
    return render(request, 'consultantdb/consultant_form.html', {'form': form, 'title': 'Update Consultant'})

def delete_consultant(request, pk):
    consultant = get_object_or_404(Consultant, pk=pk)
    if request.method == 'POST':
        consultant.delete()
        messages.success(request, "Consultant deleted successfully!")
        return redirect('consultant_list')
    return render(request, 'consultantdb/consultant_confirm_delete.html', {'consultant': consultant})

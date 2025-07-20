from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Consultant
from .forms import ConsultantForm
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def consultant_list(request):
    query = request.GET.get('q')
    consultant_list = Consultant.objects.all().order_by('-id')

    if query:
        consultant_list = consultant_list.filter(
            Q(name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone_number__icontains=query)
        )

    paginator = Paginator(consultant_list, 10)  # Show 10 consultants per page
    page = request.GET.get('page')

    try:
        consultants = paginator.page(page)
    except PageNotAnInteger:
        consultants = paginator.page(1)
    except EmptyPage:
        consultants = paginator.page(paginator.num_pages)

    return render(request, 'consultantdb/consultant_list.html', {'consultants': consultants, 'query': query})

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
from django.db import transaction

def delete_all_consultants(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                Consultant.objects.all().delete()
            messages.success(request, "All consultants have been successfully deleted.")
        except Exception as e:
            messages.error(request, f"An error occurred while deleting consultants: {e}")
    return redirect('consultant_list')

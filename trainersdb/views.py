from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Trainer
from .forms import TrainerForm
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from coursedb.models import Course

def trainer_list(request):
    query = request.GET.get('q')
    stack_query = request.GET.get('stack')
    location_query = request.GET.get('location')
    experience_query = request.GET.get('experience')
    employment_query = request.GET.get('employment')
    mode_query = request.GET.get('mode')
    availability_query = request.GET.get('availability')
    is_active_query = request.GET.get('is_active')

    trainer_list = Trainer.objects.all().order_by('-id')

    if query:
        trainer_list = trainer_list.filter(
            Q(name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone_number__icontains=query)
        )

    if stack_query:
        trainer_list = trainer_list.filter(stack__id=stack_query)

    if location_query:
        trainer_list = trainer_list.filter(location=location_query)
        
    if experience_query:
        trainer_list = trainer_list.filter(years_of_experience__gte=experience_query)


    if employment_query:
        trainer_list = trainer_list.filter(employment_type=employment_query)

    if mode_query:
        trainer_list = trainer_list.filter(mode_of_delivery__icontains=mode_query)

    if availability_query:
        trainer_list = trainer_list.filter(availability__icontains=availability_query)

    if is_active_query:
        if is_active_query == 'yes':
            trainer_list = trainer_list.filter(is_active=True)
        elif is_active_query == 'no':
            trainer_list = trainer_list.filter(is_active=False)

    paginator = Paginator(trainer_list, 10)
    page = request.GET.get('page')

    try:
        trainers = paginator.page(page)
    except PageNotAnInteger:
        trainers = paginator.page(1)
    except EmptyPage:
        trainers = paginator.page(paginator.num_pages)

    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']

    all_courses = Course.objects.all()
    location_choices = Trainer.TAMIL_NADU_LOCATIONS
    employment_choices = Trainer.EMPLOYMENT_TYPE_CHOICES
    mode_choices = [
        ('Online', 'Online'),
        ('Offline', 'Offline'),
        ('Online/Offline', 'Online/Offline')
    ]
    availability_choices = [
        ('WD', 'WD'),
        ('WE', 'WE'),
        ('WD/WE', 'WD/WE')
    ]

    context = {
        'trainers': trainers,
        'query': query or '',
        'stack_query': stack_query,
        'location_query': location_query,
        'experience_query': experience_query,
        'employment_query': employment_query,
        'mode_query': mode_query,
        'availability_query': availability_query,
        'is_active_query': is_active_query,
        'all_courses': all_courses,
        'location_choices': location_choices,
        'employment_choices': employment_choices,
        'mode_choices': mode_choices,
        'availability_choices': availability_choices,
        'query_params': query_params.urlencode(),
    }
    return render(request, 'trainersdb/trainer_list.html', context)

from .forms import TrainerForm
import json

def create_trainer(request):
    if request.method == 'POST':
        form = TrainerForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            messages.success(request, f"Trainer {form.cleaned_data.get('name')} added.")
            return redirect('trainer_list')
    else:
        form = TrainerForm()
    return render(request, 'trainersdb/create_trainer.html', {'form': form})

def update_trainer(request, pk):
    trainer = get_object_or_404(Trainer, pk=pk)
    if request.method == 'POST':
        form = TrainerForm(request.POST, request.FILES, instance=trainer)
        if form.is_valid():
            form.save()
            messages.success(request, "Trainer updated successfully!")
            return redirect('trainer_list')
    else:
        form = TrainerForm(instance=trainer)
    return render(request, 'trainersdb/update_trainer.html', {'form': form, 'title': 'Update Trainer'})

def delete_trainer(request, pk):
    trainer = get_object_or_404(Trainer, pk=pk)
    if request.method == 'POST':
        trainer.delete()
        messages.success(request, "Trainer deleted successfully!")
        return redirect('trainer_list')
    return render(request, 'trainersdb/trainer_confirm_delete.html', {'trainer': trainer})
from django.db import transaction

def delete_all_trainers(request):
    if request.method == 'POST':
        try:
            with transaction.atomic():
                Trainer.objects.all().delete()
            messages.success(request, "All trainers have been successfully deleted.")
        except Exception as e:
            messages.error(request, f"An error occurred while deleting all trainers: {e}")
    return redirect('trainer_list')

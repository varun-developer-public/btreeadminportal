from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Trainer
from .forms import TrainerForm
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def trainer_list(request):
    query = request.GET.get('q')
    trainer_list = Trainer.objects.all().order_by('-id')

    if query:
        trainer_list = trainer_list.filter(
            Q(name__icontains=query) |
            Q(email__icontains=query) |
            Q(phone__icontains=query) |
            Q(stack__icontains=query)
        )

    paginator = Paginator(trainer_list, 10)  # Show 10 trainers per page
    page = request.GET.get('page')

    try:
        trainers = paginator.page(page)
    except PageNotAnInteger:
        trainers = paginator.page(1)
    except EmptyPage:
        trainers = paginator.page(paginator.num_pages)

    return render(request, 'trainersdb/trainer_list.html', {'trainers': trainers, 'query': query})

def create_trainer(request):
    if request.method == 'POST':
        form = TrainerForm(request.POST)
        if form.is_valid():
            trainer = form.save()
            messages.success(request, f"Trainer {trainer.name} added.")
            return redirect('trainer_list')
    else:
        form = TrainerForm()
    return render(request, 'trainersdb/create_trainer.html', {'form': form})

def update_trainer(request, pk):
    trainer = get_object_or_404(Trainer, pk=pk)
    if request.method == 'POST':
        form = TrainerForm(request.POST, instance=trainer)
        if form.is_valid():
            form.save()
            messages.success(request, "Trainer updated successfully!")
            return redirect('trainer_list')
    else:
        form = TrainerForm(instance=trainer)
    return render(request, 'trainersdb/create_trainer.html', {'form': form, 'title': 'Update Trainer'})

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
            messages.error(request, f"An error occurred while deleting trainers: {e}")
    return redirect('trainer_list')

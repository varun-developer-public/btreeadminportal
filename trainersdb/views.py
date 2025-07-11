from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Trainer
from .forms import TrainerForm

def trainer_list(request):
    trainers = Trainer.objects.all()
    return render(request, 'trainersdb/trainer_list.html', {'trainers': trainers})

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

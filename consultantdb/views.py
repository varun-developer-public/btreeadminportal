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
    return render(request, 'consultantdb/create_consultant.html', {'form': form, 'title': 'Add Consultant'})

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
    return render(request, 'consultantdb/update_consultant.html', {'form': form, 'title': 'Update Consultant'})

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

from django.views.generic.edit import UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from .models import Consultant, ConsultantProfile
from .forms import ConsultantProfileForm
from django.urls import reverse_lazy

class ConsultantProfileUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
    model = Consultant
    form_class = ConsultantProfileForm
    template_name = 'consultantdb/consultant_profile_form.html'
    success_url = reverse_lazy('consultant_profile')

    def test_func(self):
        return self.request.user.role == 'consultant'

    def get_object(self, queryset=None):
        profile = get_object_or_404(ConsultantProfile, user=self.request.user)
        return get_object_or_404(Consultant, pk=profile.consultant.pk)

    def form_valid(self, form):
        form.save()
        messages.success(self.request, "Your profile has been updated successfully.")
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method == 'POST':
            kwargs['files'] = self.request.FILES
        return kwargs

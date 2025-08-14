from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.forms import inlineformset_factory
from .models import Company, ApplyingRole
from .forms import CompanyForm, ApplyingRoleForm

@login_required
def company_list(request):
    companies = Company.objects.all()
    return render(request, 'placementdrive/company_list.html', {'companies': companies})

@login_required
def company_create(request):
    ApplyingRoleFormSet = inlineformset_factory(Company, ApplyingRole, form=ApplyingRoleForm, extra=1, can_delete=True)
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        formset = ApplyingRoleFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            company = form.save(commit=False)
            company.created_by = request.user
            company.save()
            instances = formset.save(commit=False)
            for instance in instances:
                instance.created_by = request.user
                instance.company = company
                instance.save()
            formset.save_m2m()
            return redirect('placementdrive:company_list')
    else:
        form = CompanyForm()
        formset = ApplyingRoleFormSet()
    return render(request, 'placementdrive/company_form.html', {'form': form, 'formset': formset})

@login_required
def company_update(request, pk):
    company = get_object_or_404(Company, pk=pk)
    ApplyingRoleFormSet = inlineformset_factory(Company, ApplyingRole, form=ApplyingRoleForm, extra=1, can_delete=True)
    if request.method == 'POST':
        form = CompanyForm(request.POST, instance=company)
        formset = ApplyingRoleFormSet(request.POST, instance=company)
        if form.is_valid() and formset.is_valid():
            form.save()
            formset.save()
            return redirect('placementdrive:company_list')
    else:
        form = CompanyForm(instance=company)
        formset = ApplyingRoleFormSet(instance=company)
    return render(request, 'placementdrive/company_form.html', {'form': form, 'formset': formset})

@login_required
def company_delete(request, pk):
    company = get_object_or_404(Company, pk=pk)
    if request.method == 'POST':
        company.delete()
        return redirect('placementdrive:company_list')
    return render(request, 'placementdrive/company_confirm_delete.html', {'company': company})
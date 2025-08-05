from .models import Placement
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import PlacementUpdateForm, PlacementFilterForm
from django.db.models import Q
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

@login_required
def placement_list(request):
    placements = Placement.objects.select_related('student').all().order_by('-student__student_id')
    form = PlacementFilterForm(request.GET)

    if form.is_valid():
        q = form.cleaned_data.get('q')
        ug_degree = form.cleaned_data.get('ug_degree')
        ug_branch = form.cleaned_data.get('ug_branch')
        ug_passout = form.cleaned_data.get('ug_passout')
        pg_degree = form.cleaned_data.get('pg_degree')
        pg_branch = form.cleaned_data.get('pg_branch')
        pg_passout = form.cleaned_data.get('pg_passout')
        batch_id = form.cleaned_data.get('batch_id')
        course_category = form.cleaned_data.get('course_category')
        course = form.cleaned_data.get('course')
        course_status = form.cleaned_data.get('course_status')
        location = form.cleaned_data.get('location')
        course_percentage = form.cleaned_data.get('course_percentage')
        resume_status = form.cleaned_data.get('resume_status')
        is_active = form.cleaned_data.get('is_active')

        if q:
            placements = placements.filter(
                Q(student__first_name__icontains=q) |
                Q(student__last_name__icontains=q) |
                Q(student__student_id__icontains=q) |
                Q(student__phone__icontains=q)
            )
        if ug_degree:
            placements = placements.filter(student__ugdegree__icontains=ug_degree)
        if ug_branch:
            placements = placements.filter(student__ugbranch__icontains=ug_branch)
        if ug_passout:
            placements = placements.filter(student__ugpassout=ug_passout)
        if pg_degree:
            placements = placements.filter(student__pgdegree__icontains=pg_degree)
        if pg_branch:
            placements = placements.filter(student__pgbranch__icontains=pg_branch)
        if pg_passout:
            placements = placements.filter(student__pgpassout=pg_passout)
        if batch_id:
            placements = placements.filter(student__batches__batch_id__icontains=batch_id)
        if course_category:
            placements = placements.filter(student__course__category=course_category)
        if course:
            placements = placements.filter(student__course=course)
        if course_status:
            placements = placements.filter(student__course_status=course_status)
        if location:
            placements = placements.filter(student__location__icontains=location)
        if course_percentage is not None:
            placements = placements.filter(student__course_percentage=course_percentage)
        if resume_status:
            if resume_status == 'yes':
                placements = placements.filter(resume_link__isnull=False).exclude(resume_link='')
            elif resume_status == 'no':
                placements = placements.filter(Q(resume_link__isnull=True) | Q(resume_link=''))
        if is_active:
            if is_active == 'yes':
                placements = placements.filter(is_active=True)
            elif is_active == 'no':
                placements = placements.filter(is_active=False)

    paginator = Paginator(placements, 10)  # Show 10 placements per page
    page = request.GET.get('page')

    try:
        placements = paginator.page(page)
    except PageNotAnInteger:
        placements = paginator.page(1)
    except EmptyPage:
        placements = paginator.page(paginator.num_pages)

    return render(request, 'placementdb/placement_list.html', {
        'placements': placements,
        'form': form,
        'query_params': request.GET.urlencode(),
    })

from .forms import PlacementUpdateForm, CompanyInterviewForm
from placementdrive.models import PlacementDrive
import json

@login_required
def update_placement(request, pk):
    placement = get_object_or_404(Placement, pk=pk)
    interview_form = CompanyInterviewForm()

    if request.method == 'POST':
        if 'update_placement' in request.POST:
            form = PlacementUpdateForm(request.POST, request.FILES, instance=placement)
            if form.is_valid():
                form.save()
                messages.success(request, "Placement updated successfully.")
                return redirect('placement_list')
        elif 'add_interview' in request.POST:
            interview_form = CompanyInterviewForm(request.POST)
            if interview_form.is_valid():
                interview = interview_form.save(commit=False)
                interview.placement = placement
                interview.save()
                messages.success(request, "Interview added successfully.")
                return redirect('update_placement', pk=pk)

    form = PlacementUpdateForm(instance=placement)
    interviews = placement.interviews.all()
    
    companies = PlacementDrive.objects.all()
    company_details = {
        c.id: {
            'name': c.company_name,
            'location': c.location,
        } for c in companies
    }

    return render(request, 'placementdb/update_placement.html', {
        'form': form,
        'interview_form': interview_form,
        'placement': placement,
        'interviews': interviews,
        'company_details_json': json.dumps(company_details)
    })

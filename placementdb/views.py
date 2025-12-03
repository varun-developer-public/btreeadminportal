from studentsdb.forms import StudentPlacementForm
from .models import Placement, CompanyInterview
# from .models import Company
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .forms import PlacementUpdateForm, PlacementFilterForm, CompanyInterviewForm
from django.db.models import Q, Count
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from placementdrive.models import Company
import json
from django.http import JsonResponse

@login_required
def placement_list(request):
    placements = Placement.objects.select_related('student').prefetch_related('student__batches', 'student__batches__trainer').all().order_by('-student__student_id').annotate(interview_count=Count('student__interview_statuses__interview__company', distinct=True))
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
        interview_count = form.cleaned_data.get('interview_count')
        status = form.cleaned_data.get('status')
        course_start_from = form.cleaned_data.get('course_start_from')
        course_start_to = form.cleaned_data.get('course_start_to')
        course_end_from = form.cleaned_data.get('course_end_from')
        course_end_to = form.cleaned_data.get('course_end_to')

        if status:
            placements = placements.filter(**{f'student__{status}': True})
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
            placements = placements.filter(student__batches__batch_id__icontains=batch_id).distinct()
        if course_category:
            course_ids = course_category.courses.values_list('id', flat=True)
            placements = placements.filter(student__course_id__in=course_ids)
        if course:
            placements = placements.filter(student__course_id=course.id)
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
        if interview_count is not None:
            placements = placements.filter(interview_count=interview_count)

        if course_start_from:
            placements = placements.filter(student__start_date__gte=course_start_from)
        if course_start_to:
            placements = placements.filter(student__start_date__lte=course_start_to)
        if course_end_from:
            placements = placements.filter(student__end_date__gte=course_end_from)
        if course_end_to:
            placements = placements.filter(student__end_date__lte=course_end_to)

    # Process batches to get unique trainers and batch IDs
    for placement in placements:
        batches = placement.student.batches.all()
        unique_trainers = {batch.trainer for batch in batches if batch.trainer}
        unique_batches = {batch for batch in batches}
        placement.unique_trainers = list(unique_trainers)
        placement.unique_batches = list(unique_batches)
        placement.active_batch_ids = list(placement.student.batchstudent_set.filter(is_active=True).values_list('batch_id', flat=True))

    paginator = Paginator(placements, 10)
    page = request.GET.get('page')

    try:
        placements_paginated = paginator.page(page)
    except PageNotAnInteger:
        placements_paginated = paginator.page(1)
    except EmptyPage:
        placements_paginated = paginator.page(paginator.num_pages)

    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']

    return render(request, 'placementdb/placement_list.html', {
        'placements': placements_paginated,
        'form': form,
        'query_params': query_params.urlencode(),
    })

@login_required
def pending_resumes_list(request):
    placements = Placement.objects.select_related('student').filter(Q(resume_link__isnull=True) | Q(resume_link='')).order_by('-student__student_id')
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
        is_active = form.cleaned_data.get('is_active')
        course_start_from = form.cleaned_data.get('course_start_from')
        course_start_to = form.cleaned_data.get('course_start_to')
        course_end_from = form.cleaned_data.get('course_end_from')
        course_end_to = form.cleaned_data.get('course_end_to')

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
            placements = placements.filter(student__batches__batch_id__icontains=batch_id).distinct()
        if course_category:
            course_ids = course_category.courses.values_list('id', flat=True)
            placements = placements.filter(student__course_id__in=course_ids)
        if course:
            placements = placements.filter(student__course_id=course.id)
        if course_status:
            placements = placements.filter(student__course_status=course_status)
        if location:
            placements = placements.filter(student__location__icontains=location)
        if course_percentage is not None:
            placements = placements.filter(student__course_percentage=course_percentage)
        if is_active:
            if is_active == 'yes':
                placements = placements.filter(is_active=True)
            elif is_active == 'no':
                placements = placements.filter(is_active=False)

        if course_start_from:
            placements = placements.filter(student__start_date__gte=course_start_from)
        if course_start_to:
            placements = placements.filter(student__start_date__lte=course_start_to)
        if course_end_from:
            placements = placements.filter(student__end_date__gte=course_end_from)
        if course_end_to:
            placements = placements.filter(student__end_date__lte=course_end_to)

    paginator = Paginator(placements, 10)
    page = request.GET.get('page')

    try:
        placements = paginator.page(page)
    except PageNotAnInteger:
        placements = paginator.page(1)
    except EmptyPage:
        placements = paginator.page(paginator.num_pages)

    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']

    return render(request, 'placementdb/placement_list.html', {
        'placements': placements,
        'form': form,
        'query_params': query_params.urlencode(),
        'list_title': 'Students with Pending Resumes'
    })

@login_required
def update_placement(request, pk):
    placement = get_object_or_404(Placement, pk=pk)
    student = placement.student

    if request.method == 'POST':
        placement_form = PlacementUpdateForm(request.POST, request.FILES, instance=placement)
        student_form = StudentPlacementForm(request.POST, instance=student)
        
        if placement_form.is_valid() and student_form.is_valid():
            placement_form.save()
            student_form.save()
            messages.success(request, "Placement updated successfully.")
            return redirect('placementdb:placement_list')
        
    else:
        placement_form = PlacementUpdateForm(instance=placement)
        student_form = StudentPlacementForm(instance=student)
        
    interviews = placement.interviews.all()

    return render(request, 'placementdb/update_placement.html', {
        'placement_form': placement_form,
        'student_form': student_form,
        'placement': placement,
        'interviews': interviews,
    })

@login_required
def update_interview(request, pk):
    interview = get_object_or_404(CompanyInterview, pk=pk)
    if request.method == 'POST':
        form = CompanyInterviewForm(request.POST, instance=interview)
        if form.is_valid():
            form.save()
            messages.success(request, "Interview updated successfully.")
            return redirect('placementdb:update_placement', pk=interview.placement.pk)
    else:
        form = CompanyInterviewForm(instance=interview)
    return render(request, 'placementdb/update_interview.html', {'form': form})

@login_required
def delete_placement(request, pk):
    placement = get_object_or_404(Placement, pk=pk)
    if request.method == 'POST':
        placement.delete()
        messages.success(request, "Placement deleted successfully.")
        return redirect('placementdb:placement_list')
    return render(request, 'placementdb/placement_confirm_delete.html', {'placement': placement})

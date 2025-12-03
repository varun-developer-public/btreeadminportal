from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from .models import Company, Interview, InterviewStudent, ResumeSharedStatus
from .forms import CompanyForm, InterviewScheduleForm, InterviewStudentForm, CompanyFilterForm, ResumeSharedStatusForm, InterviewFilterForm
from studentsdb.models import Student
from coursedb.models import Course
from placementdb.models import CompanyInterview
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Prefetch, Subquery, OuterRef, DateTimeField
from django.db.models.functions import Coalesce, Greatest, TruncDate
from django.contrib import messages
import json
from datetime import time, datetime

# Custom JSON encoder to handle time objects
class TimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, time):
            return obj.strftime('%H:%M:%S')
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

@login_required
def company_list(request):
    # Prefetch selected students for companies with completed interviews
    selected_students_prefetch = Prefetch(
        'scheduled_interviews__student_status',
        queryset=InterviewStudent.objects.filter(status='placed').select_related('student'),
        to_attr='placed_students_list'
    )

    companies = Company.objects.prefetch_related(selected_students_prefetch, 'resume_shared_statuses','scheduled_interviews__courses').order_by('-created_at')
    form = CompanyFilterForm(request.GET or None)

    if form.is_valid():
        q = form.cleaned_data.get('q')
        progress = form.cleaned_data.get('progress')
        resume_shared_status = form.cleaned_data.get('resume_shared_status')
        domain = form.cleaned_data.get('domain')
        location = form.cleaned_data.get('location')
        created_by = form.cleaned_data.get('created_by')
        company_stack = form.cleaned_data.get('company_stack')
        created_from = form.cleaned_data.get('created_from')
        created_to = form.cleaned_data.get('created_to')
        updated_from = form.cleaned_data.get('updated_from')
        updated_to = form.cleaned_data.get('updated_to')
        interview_from = form.cleaned_data.get('interview_from')
        interview_to = form.cleaned_data.get('interview_to')


        if created_from and created_to:
            companies = companies.filter(created_at__date__range=(created_from, created_to)).distinct()

        if updated_from and updated_to:
            latest_resume_subq = ResumeSharedStatus.objects.filter(company=OuterRef('pk')).order_by('-created_at').values('created_at')[:1]
            latest_interview_subq = Interview.objects.filter(company=OuterRef('pk')).order_by('-created_at').values('created_at')[:1]

            companies = companies.annotate(
                latest_resume_created_at=Subquery(latest_resume_subq, output_field=DateTimeField()),
                latest_interview_created_at=Subquery(latest_interview_subq, output_field=DateTimeField()),
                latest_update=Greatest(
                    'created_at',
                    Coalesce('latest_resume_created_at', 'created_at'),
                    Coalesce('latest_interview_created_at', 'created_at'),
                ),
                latest_update_date=TruncDate('latest_update')
            ).filter(latest_update_date__range=(updated_from, updated_to)).distinct()

        if interview_from and interview_to:
            companies = companies.filter(
                scheduled_interviews__interview_date__range=(interview_from, interview_to)
            ).distinct()
        if q:
            companies = companies.filter(
                Q(company_name__icontains=q) |
                Q(spoc__icontains=q) |
                Q(email__icontains=q) |
                Q(location__icontains=q) |
                Q(company_code__icontains=q) |
                Q(mobile__icontains=q)
            )
        if progress:
            companies = companies.filter(progress=progress)
        if resume_shared_status:
            if resume_shared_status == 'none':
                companies = companies.filter(resume_shared_statuses__isnull=True).distinct()
            else:
                companies = companies.filter(
                    resume_shared_statuses__status=resume_shared_status
                ).distinct()
        if domain:
            companies = companies.filter(email__icontains=domain)
        if location:
            companies = companies.filter(location=location)
        if created_by:
            companies = companies.filter(created_by=created_by)
        if company_stack:
            # Split company_stack into course IDs and role strings
            course_ids = []
            role_values = []
            
            for item in company_stack:
                # Check if item is a digit (course ID) or string (role)
                if str(item).isdigit():
                    course_ids.append(int(item))
                else:
                    role_values.append(item)
            
            # Build the query
            query = Q()
            if course_ids:
                query |= Q(scheduled_interviews__courses__id__in=course_ids)
                query |= Q(resume_shared_statuses__courses__id__in=course_ids)
            if role_values:
                query |= Q(resume_shared_statuses__role__in=role_values)
                
            companies = companies.filter(query).distinct()

    paginator = Paginator(companies, 10)
    page = request.GET.get('page')

    try:
        companies = paginator.page(page)
    except PageNotAnInteger:
        companies = paginator.page(1)
    except EmptyPage:
        companies = paginator.page(paginator.num_pages)

    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']

    for company in companies:
        print( company.progress, company.resume_shared_statuses.exists())
        if company.progress == 'interview_completed':
            # Flatten the list of selected students from all interviews
            selected_students = []
            for interview in company.scheduled_interviews.all():
                if hasattr(interview, 'placed_students_list'):
                    for student_status in interview.placed_students_list:
                        # Check if the student is already in the list
                        if not any(s.student.id == student_status.student.id for s in selected_students):
                            selected_students.append(student_status)
            company.placed_students = selected_students
        else:
            company.selected_students = []

        # if company.progress == 'resume_shared' or company.resume_shared_statuses.exists():
        #     company.has_resume_shared_statuses = True
        # else:
        #     company.has_resume_shared_statuses = False
        
        # Only True if actual resume_shared data exists
        company.has_resume_shared_statuses = company.resume_shared_statuses.exists()

        
        unique_courses = []
        seen = set()
        for interview in company.scheduled_interviews.all():
            for course in interview.courses.all():
                if course.course_name not in seen:
                    seen.add(course.course_name)
                    unique_courses.append(course.course_name)
        
        # Add courses from resume shared statuses
        for status in company.resume_shared_statuses.all():
            for course in status.courses.all():
                if course.course_name not in seen:
                    seen.add(course.course_name)
                    unique_courses.append(course.course_name)
                
        company.unique_courses = unique_courses

        # Compute latest update timestamp across company creation, resume shared statuses, and interviews
        latest_resume = None
        try:
            latest_resume = company.resume_shared_statuses.all()[0] if company.resume_shared_statuses.all() else None
        except Exception:
            latest_resume = company.resume_shared_statuses.order_by('-created_at').first()

        latest_interview = company.scheduled_interviews.order_by('-created_at').first()

        candidates = [
            (company.created_at, company.created_by)
        ]

        if latest_resume:
            candidates.append((latest_resume.created_at, latest_resume.created_by))

        if latest_interview:
            candidates.append((latest_interview.created_at, latest_interview.created_by))

        company.latest_update_at, company.latest_updated_by = max(
            candidates, key=lambda x: x[0]
        )
        
    return render(request, 'placementdrive/company_list.html', {
        'companies': companies,
        'form': form,
        'query_params': query_params.urlencode(),
    })

@login_required
def interview_list(request):
    from django.utils import timezone
    from django.db.models import Max, F

    qs = Interview.objects.filter(
        interview_date__gte=timezone.now().date()
    ).annotate(
        latest_round=Max('company__scheduled_interviews__round_number')
    ).filter(
        round_number=F('latest_round')
    ).select_related('company').prefetch_related('student_status__student', 'courses')\
     .order_by('interview_date', 'interview_time')

    form = InterviewFilterForm(request.GET or None)
    if form.is_valid():
        q = form.cleaned_data.get('q')
        interview_round = form.cleaned_data.get('interview_round')
        venue = form.cleaned_data.get('venue')
        location = form.cleaned_data.get('location')
        courses = form.cleaned_data.get('courses')
        start_date = form.cleaned_data.get('start_date')
        end_date = form.cleaned_data.get('end_date')

        if q:
            qs = qs.filter(Q(company__company_name__icontains=q) | Q(applying_role__icontains=q))
        if interview_round:
            qs = qs.filter(interview_round=interview_round)
        if venue:
            qs = qs.filter(venue=venue)
        if location:
            qs = qs.filter(location=location)
        if courses and courses.exists():
            qs = qs.filter(courses__in=courses).distinct()
        if start_date and end_date:
            qs = qs.filter(interview_date__range=(start_date, end_date))

    paginator = Paginator(qs, 10)
    page = request.GET.get('page')
    try:
        interviews = paginator.page(page)
    except PageNotAnInteger:
        interviews = paginator.page(1)
    except EmptyPage:
        interviews = paginator.page(paginator.num_pages)

    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']

    selected_course_ids = request.GET.getlist('courses')

    return render(request, 'placementdrive/interview_list.html', {
        'interviews': interviews,
        'form': form,
        'query_params': query_params.urlencode(),
        'selected_course_ids': selected_course_ids,
    })

@login_required
def company_create(request):
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            company = form.save(commit=False)
            company.created_by = request.user
            company.save()
            form.save()
            return redirect('company_list')
    else:
        form = CompanyForm()
    return render(request, 'placementdrive/company_create_form.html', {'form': form})



@login_required
def add_interview_round(request, parent_interview_pk):
    parent_interview = get_object_or_404(Interview, pk=parent_interview_pk)
    company = parent_interview.company
    if request.method == 'POST':
        form = InterviewScheduleForm(request.POST, parent_interview=parent_interview)
        if form.is_valid():
            interview = form.save(commit=False)
            interview.company = company
            interview.parent_interview = parent_interview
            interview.round_number = parent_interview.round_number + 1
            interview.cycle_number = parent_interview.cycle_number
            interview.created_by = request.user
            interview.save()
            
            # Add courses from parent interview
            interview.courses.set(parent_interview.courses.all())

            students = form.cleaned_data['students']
            for student in students:
                InterviewStudent.objects.create(interview=interview, student=student)

            return redirect('company_update', pk=company.pk)
    else:
        form = InterviewScheduleForm(parent_interview=parent_interview)
    
    return render(request, 'placementdrive/add_interview_round.html', {'form': form, 'parent_interview': parent_interview})

from django.forms import modelformset_factory

@login_required
def update_interview_students(request, interview_pk):
    interview = get_object_or_404(Interview, pk=interview_pk)
    InterviewStudentFormSet = modelformset_factory(InterviewStudent, form=InterviewStudentForm, extra=0)
    
    # Get the queryset and order it
    queryset = InterviewStudent.objects.filter(interview=interview).order_by('student__student_id')

    # Search and Filter
    search_query = request.GET.get('q')
    status_filter = request.GET.get('status')

    if search_query:
        queryset = queryset.filter(
            Q(student__student_id__icontains=search_query) |
            Q(student__first_name__icontains=search_query) |
            Q(student__last_name__icontains=search_query)
        )

    if status_filter:
        queryset = queryset.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(queryset, 10)  # 10 students per page
    page = request.GET.get('page')
    try:
        students_page = paginator.page(page)
    except PageNotAnInteger:
        students_page = paginator.page(1)
    except EmptyPage:
        students_page = paginator.page(paginator.num_pages)

    if request.method == 'POST':
        formset = InterviewStudentFormSet(request.POST, request.FILES, queryset=queryset)
        if formset.is_valid():
            formset.save()
            return redirect('company_update', pk=interview.company.pk)
    else:
        # We need to pass the paginated queryset to the formset
        formset = InterviewStudentFormSet(queryset=students_page.object_list)
    
    return render(request, 'placementdrive/update_interview_students.html', {
        'formset': formset,
        'interview': interview,
        'students_page': students_page,
        'search_query': search_query or "",
        'status_filter': status_filter or ""
    })
@login_required
def remove_interview_student(request, student_interview_pk):
    student_interview = get_object_or_404(InterviewStudent, pk=student_interview_pk)
    interview_pk = student_interview.interview.pk
    
    if not request.user.is_superuser:
        messages.error(request, "You don't have permission to perform this action.")
        return redirect('update_interview_students', interview_pk=interview_pk)

    if request.method == 'POST':
        student_interview.delete()
        messages.success(request, "Student removed successfully.")
        return redirect('update_interview_students', interview_pk=interview_pk)
    
    return render(request, 'placementdrive/remove_interview_student_confirm.html', {
        'student_interview': student_interview
    })

@login_required
def company_update(request, pk):
    company = get_object_or_404(Company, pk=pk)
    interview_form = InterviewScheduleForm(request.POST or None, company=company)
    form = CompanyForm(request.POST or None, instance=company)
    resume_shared_status_form = ResumeSharedStatusForm(request.POST or None)

    if request.method == 'POST':
        if 'schedule_interview' in request.POST:
            if interview_form.is_valid():
                interview = interview_form.save(commit=False)
                interview.company = company
                interview.created_by = request.user
                
                current_cycle = company.interview_cycles
                
                existing_rounds = Interview.objects.filter(company=company, cycle_number=current_cycle).count()
                interview.round_number = existing_rounds + 1
                interview.cycle_number = current_cycle
                
                # Save company progress
                company.progress = 'interview_scheduling'
                company.save()

                # Save interview and M2M
                interview.save()
                interview_form.save_m2m()

                # Add students
                students = interview_form.cleaned_data['students']
                for student in students:
                    InterviewStudent.objects.create(interview=interview, student=student)

                messages.success(request, "Interview scheduled successfully!")
                return redirect('company_update', pk=company.pk)
        elif 'save_resume_status' in request.POST:
            if resume_shared_status_form.is_valid():
                status = resume_shared_status_form.save(commit=False)
                status.company = company
                status.created_by = request.user
                status.save()
                # Save the many-to-many relationship for courses
                messages.success(request, "Resume status saved successfully!")
                resume_shared_status_form.save_m2m()
                return redirect('company_update', pk=company.pk)
        else:
            if form.is_valid():
                company = form.save(commit=False)
                if company.progress == 'interview_not_conducted':
                    reason = form.cleaned_data.get('reason_for_not_conducting')
                    if not reason:
                        form.add_error('reason_for_not_conducting', 'This field is required when progress is Interview Not Conducted.')
                    else:
                        latest_interview = company.scheduled_interviews.order_by('-interview_date', '-interview_time').first()
                        if latest_interview:
                            students_to_update = latest_interview.student_status.all()
                            for student_status in students_to_update:
                                student_status.status = 'not_attended'
                                student_status.reason = reason
                                student_status.save()
                        company.save()
                        return redirect('company_update', pk=company.pk)
                elif 'reason_for_not_conducting' in form.changed_data and company.progress != 'interview_not_conducted':
                     form.cleaned_data.pop('reason_for_not_conducting', None)
                     company.save()
                     return redirect('company_update', pk=company.pk)
                else:
                    company.save()
                    return redirect('company_update', pk=company.pk)

    interviews = company.scheduled_interviews.all()
    for interview in interviews:
        student_list = interview.student_status.all()
        paginator = Paginator(student_list, 10)  # 10 students per page
        page = request.GET.get(f'page_{interview.pk}')
        try:
            students_page = paginator.page(page)
        except PageNotAnInteger:
            students_page = paginator.page(1)
        except EmptyPage:
            students_page = paginator.page(paginator.num_pages)
        interview.students_page = students_page

    return render(request, 'placementdrive/company_update_form.html', {
        'company': company,
        'form': form,
        'interview_form': interview_form,
        'interviews': interviews,
        'resume_shared_status_form': resume_shared_status_form
    })

@login_required
def company_delete(request, pk):
    company = get_object_or_404(Company, pk=pk)
    if request.method == 'POST':
        company.delete()
        return redirect('company_list')
    return render(request, 'placementdrive/company_confirm_delete.html', {'company': company})

@login_required
def edit_resume_shared_status(request, status_pk):
    status = get_object_or_404(ResumeSharedStatus, pk=status_pk)
    company = status.company
    
    if request.method == 'POST':
        form = ResumeSharedStatusForm(request.POST, instance=status)
        if form.is_valid():
            status = form.save(commit=False)
            status.save()
            # Save the many-to-many relationship for courses
            form.save_m2m()
            messages.success(request, "Resume shared status updated successfully!")
            return redirect('company_list')
    else:
        form = ResumeSharedStatusForm(instance=status)
    
    return render(request, 'placementdrive/edit_resume_shared_status.html', {
        'form': form,
        'status': status,
        'company': company
    })

def load_students(request):
    course_ids_str = request.GET.get('course_ids', '')
    if course_ids_str:
        course_ids = [int(cid) for cid in course_ids_str.split(',') if cid.isdigit()]
        students = Student.objects.filter(course_id__in=course_ids, pl_required=True, placement__is_active=True).distinct()
        student_data = [{"id": s.id, "student_name": f"{s.student_id} - {s.first_name} {s.last_name or ''}"} for s in students]
        return JsonResponse(student_data, safe=False, encoder=TimeEncoder)
    return JsonResponse([], safe=False, encoder=TimeEncoder)

@login_required
def postpone_interview_round(request, interview_pk):
    interview = get_object_or_404(Interview, pk=interview_pk)
    if request.method == 'POST':
        date = request.POST.get('interview_date')
        time = request.POST.get('interview_time')
        interview.interview_date = date
        interview.interview_time = time
        interview.save()
        return redirect('company_update', pk=interview.company.pk)
    return render(request, 'placementdrive/postpone_interview.html', {'interview': interview})

@login_required
def delete_interview_round(request, interview_pk):
    interview = get_object_or_404(Interview, pk=interview_pk)
    if not request.user.is_superuser:
        return redirect('company_update', pk=interview.company.pk)

    if request.method == 'POST':
        company_pk = interview.company.pk
        interview.delete()
        return redirect('company_update', pk=company_pk)
    
    return render(request, 'placementdrive/interview_round_confirm_delete.html', {'interview': interview})


@login_required
def restart_interview_cycle(request, pk):
    company = get_object_or_404(Company, pk=pk)

    if company.progress == "interview_completed":
        company.interview_cycles += 1
        company.progress = 'interview_scheduling'
        company.save()

        messages.success(request, "Interview cycle restarted. You can schedule new interviews.")
    else:
        messages.warning(request, "Interview cycle can only be restarted after completion.")

    return redirect("company_update", pk=company.pk)

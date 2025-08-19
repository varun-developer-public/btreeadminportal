from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from .models import Company, Interview, InterviewStudent
from .forms import CompanyForm, InterviewScheduleForm, InterviewStudentForm, CompanyFilterForm
from studentsdb.models import Student
from coursedb.models import Course
from placementdb.models import CompanyInterview
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q, Prefetch

def company_list(request):
    # Prefetch selected students for companies with completed interviews
    selected_students_prefetch = Prefetch(
        'scheduled_interviews__student_status',
        queryset=InterviewStudent.objects.filter(selected=True).select_related('student'),
        to_attr='selected_students_list'
    )

    companies = Company.objects.prefetch_related(selected_students_prefetch).order_by('-created_at')
    form = CompanyFilterForm(request.GET)

    if form.is_valid():
        q = form.cleaned_data.get('q')
        progress = form.cleaned_data.get('progress')

        if q:
            companies = companies.filter(
                Q(company_name__icontains=q) |
                Q(spoc__icontains=q) |
                Q(email__icontains=q) |
                Q(location__icontains=q)
            )
        if progress:
            companies = companies.filter(progress=progress)

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
        if company.progress == 'interview_completed':
            # Flatten the list of selected students from all interviews
            selected_students = []
            for interview in company.scheduled_interviews.all():
                if hasattr(interview, 'selected_students_list'):
                    for student_status in interview.selected_students_list:
                        if student_status.student not in selected_students:
                            selected_students.append(student_status.student)
            company.selected_students = selected_students
        else:
            company.selected_students = []

    return render(request, 'placementdrive/company_list.html', {
        'companies': companies,
        'form': form,
        'query_params': query_params.urlencode(),
    })

def company_create(request):
    if request.method == 'POST':
        form = CompanyForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('company_list')
    else:
        form = CompanyForm()
    return render(request, 'placementdrive/company_create_form.html', {'form': form})


def schedule_interview(request, company_pk):
    company = get_object_or_404(Company, pk=company_pk)
    if request.method == 'POST':
        form = InterviewScheduleForm(request.POST, company=company)
        if form.is_valid():
            interview = form.save(commit=False)
            interview.company = company
            interview.created_by = request.user
            interview.save()
            
            students = form.cleaned_data['students']
            for student in students:
                InterviewStudent.objects.create(interview=interview, student=student)

            company.progress = 'interview_scheduling'
            company.save()
            
            return redirect('company_update', pk=company.pk)
    return redirect('company_update', pk=company.pk)

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

def update_interview_students(request, interview_pk):
    interview = get_object_or_404(Interview, pk=interview_pk)
    if request.method == 'POST':
        for student_status in interview.student_status.all():
            selected_key = f'selected_{student_status.pk}'
            reason_key = f'reason_{student_status.pk}'
            
            student_status.selected = request.POST.get(selected_key) == 'on'
            student_status.reason = request.POST.get(reason_key, '')
            student_status.save()
        return redirect('company_update', pk=interview.company.pk)
    
    return render(request, 'placementdrive/update_interview_students.html', {'interview': interview})

def company_update(request, pk):
    company = get_object_or_404(Company, pk=pk)
    if request.method == 'POST':
        form = CompanyForm(request.POST, instance=company)
        if form.is_valid():
            form.save()
            return redirect('company_update', pk=company.pk)
    else:
        form = CompanyForm(instance=company)
    
    interview_form = InterviewScheduleForm(company=company)
    
    return render(request, 'placementdrive/company_update_form.html', {
        'company': company,
        'form': form,
        'interview_form': interview_form,
        'interviews': company.scheduled_interviews.all()
    })

def company_delete(request, pk):
    company = get_object_or_404(Company, pk=pk)
    if request.method == 'POST':
        company.delete()
        return redirect('company_list')
    return render(request, 'placementdrive/company_confirm_delete.html', {'company': company})

def load_students(request):
    course_ids_str = request.GET.get('course_ids', '')
    if course_ids_str:
        course_ids = [int(cid) for cid in course_ids_str.split(',') if cid.isdigit()]
        students = Student.objects.filter(course_id__in=course_ids, pl_required=True).distinct()
        student_data = [{"id": s.id, "student_name": f"{s.first_name} {s.last_name}"} for s in students]
        return JsonResponse(student_data, safe=False)
    return JsonResponse([], safe=False)
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from django.core.exceptions import ValidationError
import csv
import io
from django.http import HttpResponse
from django.contrib.auth.decorators import user_passes_test
from .models import Course, CourseCategory, CourseModule, Topic
from .forms import CourseForm, CourseCategoryForm
from django.db import transaction

def course_list(request):
    courses = Course.objects.prefetch_related('modules__topics').all()
    return render(request, 'coursedb/course_list.html', {'courses': courses})

def course_create(request):
    if request.method == 'POST':
        form = CourseForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    course = form.save()
                    
                    module_names = request.POST.getlist('module_name')
                    module_hours = request.POST.getlist('module_hours')
                    
                    for i in range(len(module_names)):
                        has_topics = request.POST.get(f'has_topics_module_{i}') == 'on'
                        
                        module = CourseModule.objects.create(
                            course=course,
                            name=module_names[i],
                            module_duration=module_hours[i],
                            has_topics=has_topics
                        )

                        if has_topics:
                            topic_names = request.POST.getlist(f'topic_name_module_{i}')
                            topic_hours = request.POST.getlist(f'topic_hours_module_{i}')
                            for j in range(len(topic_names)):
                                Topic.objects.create(
                                    module=module,
                                    name=topic_names[j],
                                    topic_duration=topic_hours[j]
                                )
                    
                    messages.success(request, "Course created successfully.")
                    return redirect('coursedb:course_list')
            except Exception as e:
                messages.error(request, f"An error occurred: {e}")
    else:
        form = CourseForm()

    context = {
        'form': form,
    }
    return render(request, 'coursedb/course_form.html', context)


from .forms import CourseForm, CourseCategoryForm

def course_update(request, pk):
    course = get_object_or_404(Course.objects.prefetch_related('modules__topics'), pk=pk)

    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            try:
                with transaction.atomic():
                    course = form.save()
                    
                    # Clear existing modules and topics to handle updates and deletions
                    course.modules.all().delete()

                    module_names = request.POST.getlist('module_name')
                    module_hours = request.POST.getlist('module_hours')
                    
                    for i in range(len(module_names)):
                        has_topics = request.POST.get(f'has_topics_module_{i}') == 'on'
                        
                        module = CourseModule.objects.create(
                            course=course,
                            name=module_names[i],
                            module_duration=module_hours[i],
                            has_topics=has_topics
                        )

                        if has_topics:
                            topic_names = request.POST.getlist(f'topic_name_module_{i}')
                            topic_hours = request.POST.getlist(f'topic_hours_module_{i}')
                            for j in range(len(topic_names)):
                                Topic.objects.create(
                                    module=module,
                                    name=topic_names[j],
                                    topic_duration=topic_hours[j]
                                )
                    
                    messages.success(request, "Course updated successfully.")
                    return redirect('coursedb:course_list')
            except Exception as e:
                messages.error(request, f"An error occurred: {e}")
        else:
            messages.error(request, "Please correct the errors below.")
    else:
        form = CourseForm(instance=course)

    context = {
        'form': form,
        'course': course,
    }
    return render(request, 'coursedb/course_update_form.html', context)


def course_delete(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        course.delete()
        messages.success(request, 'Course deleted successfully.')
        return redirect('coursedb:course_list')
    return render(request, 'coursedb/course_confirm_delete.html', {'object': course})

def category_list(request):
    categories = CourseCategory.objects.all()
    return render(request, 'coursedb/category_list.html', {'categories': categories})

def category_create(request):
    if request.method == 'POST':
        form = CourseCategoryForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category created successfully.')
            return redirect('coursedb:category_list')
    else:
        last_category = CourseCategory.objects.order_by('id').last()
        if last_category:
            last_id = int(last_category.code[1:])
            next_code = 'C' + str(last_id + 1)
        else:
            next_code = 'C1'
        form = CourseCategoryForm(initial={'code': next_code})
    return render(request, 'coursedb/category_form.html', {'form': form})

def category_update(request, pk):
    category = get_object_or_404(CourseCategory, pk=pk)
    if request.method == 'POST':
        form = CourseCategoryForm(request.POST, instance=category)
        if form.is_valid():
            form.save()
            messages.success(request, 'Category updated successfully.')
            return redirect('coursedb:category_list')
    else:
        form = CourseCategoryForm(instance=category)
    return render(request, 'coursedb/category_form.html', {'form': form})

def category_delete(request, pk):
    category = get_object_or_404(CourseCategory, pk=pk)
    if request.method == 'POST':
        category.delete()
        messages.success(request, 'Category deleted successfully.')
        return redirect('coursedb:category_list')
    return render(request, 'coursedb/category_confirm_delete.html', {'object': category})

def get_next_course_code(request):
    category_id = request.GET.get('category_id')
    if not category_id:
        return JsonResponse({'error': 'Category ID not provided'}, status=400)
    
    try:
        category = CourseCategory.objects.get(id=category_id)
        last_course = Course.objects.filter(category=category).order_by('id').last()
        category_code = category.code
        if last_course:
            last_id = int(last_course.code[len(category_code):])
            new_id = last_id + 1
        else:
            new_id = 1
        next_code = f"{category_code}{new_id:03d}"
        return JsonResponse({'next_code': next_code})
    except CourseCategory.DoesNotExist:
        return JsonResponse({'error': 'Category not found'}, status=404)
def is_admin(user):
    return user.is_authenticated and user.is_superuser

@user_passes_test(is_admin)
def export_courses_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="courses.csv"'

    writer = csv.writer(response)
    writer.writerow(['Category Code', 'Category Name', 'Course Code', 'Course Name', 'Total Duration', 'Module Name', 'Module Duration', 'Has Topics', 'Topic Name', 'Topic Duration'])

    for course in Course.objects.all():
        if course.modules.exists():
            for module in course.modules.all():
                if module.topics.exists():
                    for topic in module.topics.all():
                        writer.writerow([
                            course.category.code,
                            course.category.name,
                            course.code,
                            course.course_name,
                            course.total_duration,
                            module.name,
                            module.module_duration,
                            module.has_topics,
                            topic.name,
                            topic.topic_duration
                        ])
                else:
                    writer.writerow([
                        course.category.code,
                        course.category.name,
                        course.code,
                        course.course_name,
                        course.total_duration,
                        module.name,
                        module.module_duration,
                        module.has_topics,
                        '',
                        ''
                    ])
        else:
            writer.writerow([
                course.category.code,
                course.category.name,
                course.code,
                course.course_name,
                course.total_duration,
                '',
                '',
                '',
                '',
                ''
            ])
    return response

@user_passes_test(is_admin)
def import_courses_csv(request):
    if request.method == 'POST':
        csv_file = request.FILES['csv_file']
        if not csv_file.name.endswith('.csv'):
            messages.error(request, 'This is not a CSV file')
            return redirect('coursedb:course_list')

        data_set = csv_file.read().decode('UTF-8')
        io_string = io.StringIO(data_set)
        reader = csv.DictReader(io_string)
        rows = list(reader)
        errors = []

        try:
            with transaction.atomic():
                courses = {}
                for i, row in enumerate(rows):
                    try:
                        course_code = row['Course Code']
                        if course_code not in courses:
                            category_form = CourseCategoryForm({'name': row['Category Name'], 'code': row['Category Code']})
                            if not category_form.is_valid():
                                raise ValidationError(f"Row {i+2}: Category validation error: {category_form.errors.as_json()}")
                            category, _ = CourseCategory.objects.get_or_create(code=row['Category Code'], defaults={'name': row['Category Name']})

                            course_data_for_form = {
                                'course_name': row['Course Name'],
                                'code': course_code,
                                'category': category.pk,
                                'total_duration': row['Total Duration'],
                                'course_type': 'Course'
                            }
                            course_form = CourseForm(course_data_for_form)
                            if not course_form.is_valid():
                                raise ValidationError(f"Row {i+2}: Course validation error: {course_form.errors.as_json()}")
                            
                            course, created = Course.objects.update_or_create(
                                code=course_code,
                                defaults=course_form.cleaned_data
                            )
                            courses[course_code] = {'instance': course, 'modules': {}}

                        course_data = courses[course_code]
                        module_name = row['Module Name']
                        if module_name and module_name not in course_data['modules']:
                            module_form_data = {
                                'name': module_name,
                                'module_duration': row['Module Duration'],
                                'has_topics': row['Has Topics'].lower() == 'true'
                            }
                            module, created = CourseModule.objects.update_or_create(
                                course=course_data['instance'],
                                name=module_name,
                                defaults=module_form_data
                            )
                            course_data['modules'][module_name] = {'instance': module, 'topics': set()}

                        module_data = course_data['modules'][module_name]
                        topic_name = row['Topic Name']
                        if topic_name and topic_name not in module_data['topics']:
                            topic_form_data = {
                                'name': topic_name,
                                'topic_duration': row['Topic Duration']
                            }
                            Topic.objects.update_or_create(
                                module=module_data['instance'],
                                name=topic_name,
                                defaults=topic_form_data
                            )
                            module_data['topics'].add(topic_name)
                    except Exception as e:
                        row['Errors'] = str(e)
                        errors.append(row)

                if errors:
                    raise ValidationError("Errors found during import.")

            messages.success(request, "Courses imported successfully.")
            return redirect('coursedb:course_list')

        except ValidationError:
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="import_errors.csv"'
            
            fieldnames = list(rows[0].keys()) + ['Errors']
            writer = csv.DictWriter(response, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(errors)
            return response

    return render(request, 'coursedb/import_form.html')
def download_sample_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="sample_import_template.csv"'

    writer = csv.writer(response)
    writer.writerow(['Category Code', 'Category Name', 'Course Code', 'Course Name', 'Total Duration', 'Module Name', 'Module Duration', 'Has Topics', 'Topic Name', 'Topic Duration'])
    writer.writerow(['C1', 'Programming', 'C1001', 'Introduction to Python', '40', 'Module 1: Basics', '10', 'True', 'Topic 1: Variables', '5'])
    writer.writerow(['C1', 'Programming', 'C1001', 'Introduction to Python', '40', 'Module 1: Basics', '10', 'True', 'Topic 2: Data Types', '5'])
    writer.writerow(['C1', 'Programming', 'C1001', 'Introduction to Python', '40', 'Module 2: Control Flow', '15', 'False', '', ''])
    writer.writerow(['C2', 'Web Development', 'C2001', 'HTML & CSS', '20', 'Module 1: HTML', '10', 'False', '', ''])

    return response
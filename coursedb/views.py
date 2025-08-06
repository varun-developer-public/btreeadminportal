from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
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
                    
                    # This is tricky because checkboxes only submit a value when checked.
                    # We need a way to associate topics with the correct module.
                    # Let's assume the order is preserved.
                    
                    current_topic_index = 0
                    for i in range(len(module_names)):
                        # A hidden input could be added by the JS to mark which modules have topics.
                        # For now, we'll rely on the presence of topic names for a given module index.
                        has_topics_key = f'module_{i}_has_topics' # A hypothetical hidden field.
                        has_topics = request.POST.get(f'has_topics_module_{i}') == 'on' # Let's assume JS adds this.

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


def course_update(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        if form.is_valid():
            try:
                with transaction.atomic():
                    course = form.save()
                    
                    course.modules.all().delete()

                    module_names = request.POST.getlist('module_name')
                    module_hours = request.POST.getlist('module_hours')

                    for i in range(len(module_names)):
                        has_topics = f'module_{i}_has_topics' in request.POST
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
        form = CourseForm(instance=course)

    context = {'form': form, 'course': course}
    return render(request, 'coursedb/course_form.html', context)


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
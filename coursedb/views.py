from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.http import JsonResponse
from .models import Course, CourseCategory, CourseModule
from .forms import CourseForm, CourseCategoryForm, CourseModuleFormSet, TopicFormSet

def course_list(request):
    courses = Course.objects.prefetch_related('modules').all()
    return render(request, 'coursedb/course_list.html', {'courses': courses})

from django.shortcuts import render, redirect
from django.contrib import messages

def course_create(request):
    if request.method == 'POST':
        course_form = CourseForm(request.POST)
        module_formset = CourseModuleFormSet(request.POST, prefix='modules')

        all_valid = course_form.is_valid() and module_formset.is_valid()
        topic_formsets = []
        modules = module_formset.save(commit=False) if module_formset.is_valid() else []

        for i, module_form in enumerate(module_formset.forms):
            prefix = f'modules-{i}-topics'
            if (module_form.cleaned_data and 
                not module_form.cleaned_data.get('DELETE', False) and 
                module_form.cleaned_data.get('has_topics')):
                module_instance = modules[i] if i < len(modules) else None
                topic_formset = TopicFormSet(request.POST, instance=module_instance, prefix=prefix)
                topic_formsets.append(topic_formset)
                module_form.topic_formset = topic_formset
                if not topic_formset.is_valid():
                    all_valid = False
            else:
                topic_formset = TopicFormSet(request.POST, prefix=prefix)
                topic_formsets.append(None)
                module_form.topic_formset = topic_formset

        module_formset.empty_form.topic_formset = TopicFormSet(prefix=f'{module_formset.prefix}-__prefix__-topics')

        if all_valid:
            course = course_form.save()
            for i, module in enumerate(modules):
                module.course = course
                module.save()
                if topic_formsets[i]:
                    topics = topic_formsets[i].save(commit=False)
                    for topic in topics:
                        topic.module = module
                        topic.save()
            messages.success(request, "Course created successfully.")
            return redirect('coursedb:course_list')

    else:  # GET
        course_form = CourseForm()
        module_formset = CourseModuleFormSet(prefix='modules')
        for i, module_form in enumerate(module_formset.forms):
            prefix = f'modules-{i}-topics'
            module_form.topic_formset = TopicFormSet(prefix=prefix)
        module_formset.empty_form.topic_formset = TopicFormSet(prefix=f'{module_formset.prefix}-__prefix__-topics')

    context = {
        'form': course_form,
        'formset': module_formset,
    }
    return render(request, 'coursedb/course_form.html', context)

def course_update(request, pk):
    course = get_object_or_404(Course, pk=pk)
    if request.method == 'POST':
        form = CourseForm(request.POST, instance=course)
        module_formset = CourseModuleFormSet(request.POST, instance=course, prefix='modules')

        if form.is_valid() and module_formset.is_valid():
            all_valid = True
            topic_formsets = []
            for i, module_form in enumerate(module_formset.forms):
                if module_form.cleaned_data and not module_form.cleaned_data.get('DELETE'):
                    if module_form.cleaned_data.get('has_topics'):
                        prefix = f'modules-{i}-topics'
                        topic_formset = TopicFormSet(request.POST, instance=module_form.instance, prefix=prefix)
                        topic_formsets.append(topic_formset)
                        if not topic_formset.is_valid():
                            all_valid = False
                    else:
                        topic_formsets.append(None)
            
            if all_valid:
                form.save()
                module_formset.save()
                for i, module_form in enumerate(module_formset.forms):
                    if module_form.cleaned_data and not module_form.cleaned_data.get('DELETE'):
                        if topic_formsets[i]:
                            topic_formsets[i].save()
                        else:
                            module_form.instance.topics.all().delete()
                messages.success(request, "Course updated successfully.")
                return redirect('coursedb:course_list')

        # Re-render with errors
        for i, module_form in enumerate(module_formset.forms):
            prefix = f'modules-{i}-topics'
            if module_form.cleaned_data and module_form.cleaned_data.get('has_topics'):
                 module_form.topic_formset = TopicFormSet(request.POST, instance=module_form.instance, prefix=prefix)
            else:
                 module_form.topic_formset = TopicFormSet(instance=module_form.instance, prefix=prefix)
        module_formset.empty_form.topic_formset = TopicFormSet(prefix=f'{module_formset.prefix}-__prefix__-topics')

    else:  # GET
        form = CourseForm(instance=course)
        module_formset = CourseModuleFormSet(instance=course, prefix='modules')
        for i, module_form in enumerate(module_formset.forms):
            prefix = f'modules-{i}-topics'
            module_form.topic_formset = TopicFormSet(instance=module_form.instance, prefix=prefix)
        module_formset.empty_form.topic_formset = TopicFormSet(prefix=f'{module_formset.prefix}-__prefix__-topics')

    context = {'form': form, 'formset': module_formset}
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
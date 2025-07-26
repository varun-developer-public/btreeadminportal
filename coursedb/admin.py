from django.contrib import admin
from django.core.exceptions import ValidationError
from django import forms
from .models import CourseCategory, Course, CourseModule, Topic

class CourseModuleInline(admin.TabularInline):
    model = CourseModule
    extra = 1

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    inlines = [CourseModuleInline]
    list_display = ('course_name', 'course_type', 'category', 'total_duration')
    list_filter = ('course_type', 'category')
    search_fields = ('course_name',)

@admin.register(CourseCategory)
class CourseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)

class TopicInline(admin.TabularInline):
    model = Topic
    extra = 1

@admin.register(CourseModule)
class CourseModuleAdmin(admin.ModelAdmin):
    inlines = [TopicInline]
    list_display = ('name', 'course', 'module_duration', 'has_topics')
    list_filter = ('course', 'has_topics')
    search_fields = ('name',)

@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ('name', 'module', 'topic_duration')
    list_filter = ('module__course',)
    search_fields = ('name',)

import json
from django.core.management.base import BaseCommand
from django.db import transaction
from studentsdb.models import CourseCategory as OldCourseCategory, Course as OldCourse
from coursedb.models import CourseCategory as NewCourseCategory, Course as NewCourse

class Command(BaseCommand):
    help = 'Migrates course and category data from studentsdb to coursedb.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Starting course data migration...")

        category_map = {}
        course_map = {}

        # 1. Migrate CourseCategory
        self.stdout.write("Migrating course categories...")
        for old_category in OldCourseCategory.objects.all():
            new_category, created = NewCourseCategory.objects.get_or_create(
                name=old_category.name
            )
            category_map[old_category.id] = new_category.id
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Successfully created category: {new_category.name}'))
            else:
                self.stdout.write(self.style.WARNING(f'  Category already exists: {new_category.name}'))

        # 2. Migrate Course
        self.stdout.write("Migrating courses...")
        for old_course in OldCourse.objects.all():
            new_category_id = category_map.get(old_course.category_id)
            if not new_category_id:
                self.stdout.write(self.style.ERROR(f'  Could not find new category for old course: {old_course.name}'))
                continue

            new_category = NewCourseCategory.objects.get(id=new_category_id)
            
            new_course, created = NewCourse.objects.get_or_create(
                course_name=old_course.name,
                category=new_category,
                defaults={
                    'code': old_course.code,
                    'course_type': 'Course', 
                    'total_duration': 0
                }
            )
            course_map[old_course.id] = new_course.id
            if created:
                self.stdout.write(self.style.SUCCESS(f'  Successfully created course: {new_course.course_name}'))
            else:
                self.stdout.write(self.style.WARNING(f'  Course already exists: {new_course.course_name}'))

        # 3. Save the map for the next step
        with open('course_map.json', 'w') as f:
            json.dump(course_map, f)

        self.stdout.write(self.style.SUCCESS("Data migration complete. Course map saved to course_map.json."))

import json
from django.core.management.base import BaseCommand
from django.db import transaction
from studentsdb.models import Student, Course, CourseCategory
from coursedb.models import CourseCategory as NewCourseCategory, Course as NewCourse

class Command(BaseCommand):
    help = 'A full, safe migration of course data from studentsdb to coursedb.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Starting the full course data migration process...")

        # Step 1: Load the safe data from our JSON export
        self.stdout.write("Loading data from old_course_data.json...")
        try:
            with open('old_course_data.json', 'r') as f:
                data = json.load(f)
            old_courses = data['courses']
            old_categories = data['categories']
            old_course_ids = {c['id'] for c in old_courses}
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR("FATAL: old_course_data.json not found. Cannot proceed."))
            return

        # Step 2: Fix orphaned student records
        self.stdout.write("Fixing orphaned student records...")
        orphaned_students = Student.objects.exclude(course_id__in=old_course_ids).exclude(course_id__isnull=True)
        if orphaned_students.exists():
            self.stdout.write(self.style.WARNING(f"Found {orphaned_students.count()} orphaned students. Setting their course to NULL."))
            for student in orphaned_students:
                student.course = None
                student.save()
        else:
            self.stdout.write(self.style.SUCCESS("No orphaned student records found."))

        # Step 3: Migrate categories and courses to coursedb
        self.stdout.write("Migrating categories and courses to coursedb...")
        category_map = {}
        course_map = {}

        for cat_data in old_categories:
            new_category, _ = NewCourseCategory.objects.get_or_create(name=cat_data['name'])
            category_map[cat_data['id']] = new_category.id

        for course_data in old_courses:
            new_category_id = category_map.get(course_data['category_id'])
            if new_category_id:
                new_category = NewCourseCategory.objects.get(id=new_category_id)
                new_course, _ = NewCourse.objects.get_or_create(
                    course_name=course_data['name'],
                    category=new_category,
                    defaults={'code': course_data['code'], 'course_type': 'Course', 'total_duration': 0}
                )
                course_map[course_data['id']] = new_course.id
        
        self.stdout.write(self.style.SUCCESS("Data successfully migrated to coursedb."))

        # Step 4: Update student foreign keys to point to new courses
        self.stdout.write("Updating student foreign key references...")
        for student in Student.objects.filter(course_id__isnull=False):
            new_course_id = course_map.get(student.course_id)
            if new_course_id:
                student.course_id = new_course_id
                student.save()
        
        self.stdout.write(self.style.SUCCESS("Student references updated."))
        self.stdout.write(self.style.SUCCESS("Full course data migration is complete."))
import json
from django.core.management.base import BaseCommand
from django.db import transaction, connection
from studentsdb.models import Student
from coursedb.models import CourseCategory as NewCourseCategory, Course as NewCourse
from studentsdb.models import Course as OldCourse, CourseCategory as OldCourseCategory

class Command(BaseCommand):
    help = 'Fixes orphaned student records and migrates course data.'

    @transaction.atomic
    def handle(self, *args, **options):
        self.stdout.write("Starting data fixing and migration process...")

        # 1. Fix orphaned student records
        self.stdout.write("Checking for orphaned student records...")
        all_course_ids = set(OldCourse.objects.values_list('id', flat=True))
        orphaned_students = Student.objects.exclude(course_id__in=all_course_ids).exclude(course_id__isnull=True)
        
        if orphaned_students.exists():
            self.stdout.write(self.style.WARNING(f"Found {orphaned_students.count()} orphaned students."))
            for student in orphaned_students:
                self.stdout.write(f"  - Student {student.student_id} points to non-existent course {student.course_id}. Setting course to NULL.")
                student.course = None
                student.save()
        else:
            self.stdout.write(self.style.SUCCESS("No orphaned student records found."))

        # 2. Migrate data
        self.stdout.write("Migrating course data...")
        category_map = {}
        course_map = {}

        for old_category in OldCourseCategory.objects.all():
            new_category, _ = NewCourseCategory.objects.get_or_create(name=old_category.name)
            category_map[old_category.id] = new_category.id

        for old_course in OldCourse.objects.all():
            new_category_id = category_map.get(old_course.category_id)
            if new_category_id:
                new_category = NewCourseCategory.objects.get(id=new_category_id)
                new_course, _ = NewCourse.objects.get_or_create(
                    course_name=old_course.name,
                    category=new_category,
                    defaults={'code': old_course.code, 'course_type': 'Course', 'total_duration': 0}
                )
                course_map[old_course.id] = new_course.id

        self.stdout.write(self.style.SUCCESS("Course data migrated successfully."))

        # 3. Update student foreign keys
        self.stdout.write("Updating student course references...")
        for student in Student.objects.filter(course_id__isnull=False):
            new_course_id = course_map.get(student.course_id)
            if new_course_id:
                student.course_id = new_course_id
                student.save()
        
        self.stdout.write(self.style.SUCCESS("Student references updated."))
        self.stdout.write(self.style.SUCCESS("Data fixing and migration complete."))
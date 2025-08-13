import json
from django.core.management.base import BaseCommand
from django.db import transaction
from studentsdb.models import Student

class Command(BaseCommand):
    help = 'Updates student course foreign keys based on a mapping file.'

    def handle(self, *args, **options):
        self.stdout.write("Starting student course reference update...")

        try:
            with open('course_map.json', 'r') as f:
                course_map = json.load(f)
        except FileNotFoundError:
            self.stdout.write(self.style.ERROR("Error: course_map.json not found. Please run migrate_courses first."))
            return

        # We need to convert keys from string (JSON) to int
        course_map = {int(k): v for k, v in course_map.items()}

        with transaction.atomic():
            students_to_update = Student.objects.filter(course_id__isnull=False)
            updated_count = 0
            for student in students_to_update:
                old_course_id = student.course_id
                new_course_id = course_map.get(old_course_id)
                
                if new_course_id:
                    # This is tricky. We can't just update the FK because of the constraint.
                    # We need to do this in a raw query or by temporarily disabling constraints.
                    # A better approach is to create a separate data migration.
                    # For now, let's just print what would happen.
                    self.stdout.write(f"Would update student {student.student_id}: set course_id from {old_course_id} to {new_course_id}")
                    
                    # The actual update needs to happen in a data migration.
                    # We will generate that next.
                    
            self.stdout.write(self.style.WARNING("This command is for inspection. Run the data migration to apply changes."))

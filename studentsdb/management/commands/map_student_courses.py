import json
from django.core.management.base import BaseCommand
from studentsdb.models import Student

class Command(BaseCommand):
    help = 'Maps old course IDs to new course IDs for all students'

    def handle(self, *args, **options):
        with open('course_map.json', 'r') as f:
            course_map = json.load(f)

        for student in Student.objects.all():
            if student.course_id:
                old_course_id = str(student.course_id)
                if old_course_id in course_map:
                    student.course_id = course_map[old_course_id]
                    student.save()

        self.stdout.write(self.style.SUCCESS('Successfully mapped student courses.'))
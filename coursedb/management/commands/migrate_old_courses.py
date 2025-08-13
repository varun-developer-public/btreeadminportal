import json
from django.core.management.base import BaseCommand
from coursedb.models import Course, CourseCategory

class Command(BaseCommand):
    help = 'Migrates old course data from a JSON file to the database'

    def handle(self, *args, **options):
        with open('old_c_data.json', 'r') as f:
            data = json.load(f)

        categories_data = data.get('categories', [])
        for category_data in categories_data:
            CourseCategory.objects.update_or_create(
                id=category_data['id'],
                defaults={'name': category_data['name']}
            )

        courses_data = data.get('courses', [])
        for course_data in courses_data:
            category = CourseCategory.objects.get(id=course_data['category_id'])
            Course.objects.update_or_create(
                id=course_data['id'],
                defaults={
                    'course_name': course_data['name'],
                    'code': course_data['code'],
                    'category': category,
                    'total_duration': 0  # Set a default duration
                }
            )

        self.stdout.write(self.style.SUCCESS('Successfully migrated old course data.'))
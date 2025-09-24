from django.core.management.base import BaseCommand
from django.db import connection
from coursedb.models import Course
from decimal import Decimal, InvalidOperation

class Command(BaseCommand):
    help = 'Fixes courses with null or invalid total_duration'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute("SELECT id, course_name, total_duration FROM coursedb_course")
            rows = cursor.fetchall()

        for row in rows:
            course_id, course_name, total_duration_raw = row
            try:
                # Attempt to convert the raw value to a Decimal
                if total_duration_raw is None:
                    raise InvalidOperation
                Decimal(str(total_duration_raw))
            except InvalidOperation:
                self.stdout.write(self.style.WARNING(
                    f'Found invalid duration "{total_duration_raw}" for course "{course_name}" (ID: {course_id}). Fixing...'
                ))
                # Use the ORM to update the specific record safely
                Course.objects.filter(id=course_id).update(total_duration=Decimal('0.00'))

        self.stdout.write(self.style.SUCCESS('Finished fixing course durations.'))
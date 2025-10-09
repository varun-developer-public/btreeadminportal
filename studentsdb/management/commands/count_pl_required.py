from django.core.management.base import BaseCommand
from studentsdb.models import Student
from placementdb.models import Placement

class Command(BaseCommand):
    help = 'Counts students with pl_required=True and finds students in placement table with pl_required=False'

    def handle(self, *args, **options):
        # Original count
        pl_required_count = Student.objects.filter(pl_required=True).count()
        self.stdout.write(self.style.SUCCESS(f'Total students with pl_required=True: {pl_required_count}'))

        self.stdout.write(self.style.WARNING('\nChecking for inconsistencies...'))

        # Find students in Placement table but pl_required is False in Student table
        mismatched_placements = Placement.objects.filter(student__pl_required=False)
        mismatched_count = mismatched_placements.count()

        if mismatched_count > 0:
            self.stdout.write(self.style.ERROR(f'Found {mismatched_count} students in Placement table with pl_required=False:'))
            for placement in mismatched_placements:
                student = placement.student
                self.stdout.write(f'  - Student ID: {student.student_id}, Name: {student.first_name} {student.last_name}')
        else:
            self.stdout.write(self.style.SUCCESS('No inconsistencies found. All students in the placement table have pl_required=True.'))
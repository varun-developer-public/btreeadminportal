from django.core.management.base import BaseCommand
from studentsdb.models import Student, StudentConversation

class Command(BaseCommand):
    help = "Initialize StudentConversation objects for students"

    def add_arguments(self, parser):
        parser.add_argument("--active-only", action="store_true")
        parser.add_argument("--batch-size", type=int, default=500)

    def handle(self, *args, **options):
        active_only = options.get("active_only", False)
        batch_size = int(options.get("batch_size", 500)) or 500
        qs = Student.objects.all()
        if active_only:
            qs = qs.filter(course_status__in=["IP", "C", "P"])
        qs = qs.filter(conversation__isnull=True).order_by("id")
        ids = list(qs.values_list("id", flat=True))
        total = len(ids)
        created = 0
        for i in range(0, total, batch_size):
            batch_ids = ids[i:i + batch_size]
            objs = [StudentConversation(student_id=sid) for sid in batch_ids]
            StudentConversation.objects.bulk_create(objs, batch_size=batch_size, ignore_conflicts=True)
            created += len(batch_ids)
            self.stdout.write(f"Created {created}/{total}")
        self.stdout.write(self.style.SUCCESS(f"Initialized conversations for {created} students"))

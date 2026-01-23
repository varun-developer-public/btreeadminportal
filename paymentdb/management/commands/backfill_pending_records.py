from django.core.management.base import BaseCommand
from django.db import transaction
from paymentdb.models import Payment, PendingPaymentRecord

class Command(BaseCommand):
    help = 'Backfills PendingPaymentRecord for YTS and IP students with pending amounts'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true')
        parser.add_argument('--limit', type=int)

    def handle(self, *args, **options):
        dry_run = options.get('dry_run')
        limit = options.get('limit')
        payments = Payment.objects.select_related('student').filter(
            student__course_status__in=['YTS', 'IP', 'H', 'D']
        )
        if limit:
            payments = payments[:limit]
        created = 0
        updated = 0
        skipped = 0
        with transaction.atomic():
            for p in payments:
                pending_calc = p.calculate_total_pending()
                if p.total_pending_amount != pending_calc and not dry_run:
                    p.total_pending_amount = pending_calc
                    p.save(update_fields=['total_pending_amount'])
                if pending_calc <= 0:
                    skipped += 1
                    continue
                try:
                    record = p.pending_record
                    exists = True
                except PendingPaymentRecord.DoesNotExist:
                    record = PendingPaymentRecord(payment=p, student=p.student, course_status=p.student.course_status)
                    exists = False
                record.refresh_from_sources()
                record.status = 'Pending'
                if not dry_run:
                    record.save()
                if exists:
                    updated += 1
                else:
                    created += 1
        self.stdout.write(self.style.SUCCESS(f'Created: {created}, Updated: {updated}, Skipped: {skipped}'))

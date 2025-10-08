from django.core.management.base import BaseCommand
from django.utils import timezone
from batchdb.models import TransferRequest, TrainerHandover

class Command(BaseCommand):
    help = 'Expires pending requests that have passed their expiration time.'

    def handle(self, *args, **options):
        now = timezone.now()
        
        # Expire transfer requests
        expired_transfers = TransferRequest.objects.filter(
            status='PENDING',
            expires_at__lte=now
        )
        expired_transfers.update(status='EXPIRED')
        self.stdout.write(self.style.SUCCESS(f'Successfully expired {expired_transfers.count()} transfer requests.'))
        
        # Expire handover requests
        expired_handovers = TrainerHandover.objects.filter(
            status='PENDING',
            expires_at__lte=now
        )
        expired_handovers.update(status='EXPIRED')
        self.stdout.write(self.style.SUCCESS(f'Successfully expired {expired_handovers.count()} handover requests.'))
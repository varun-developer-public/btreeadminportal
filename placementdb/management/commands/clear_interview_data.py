from django.core.management.base import BaseCommand
from placementdb.models import CompanyInterview
from placementdrive.models import ApplyingRole

class Command(BaseCommand):
    help = 'Clears all data from CompanyInterview and ApplyingRole tables'

    def handle(self, *args, **options):
        self.stdout.write('Clearing CompanyInterview table...')
        CompanyInterview.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Successfully cleared CompanyInterview table.'))

        self.stdout.write('Clearing ApplyingRole table...')
        ApplyingRole.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Successfully cleared ApplyingRole table.'))

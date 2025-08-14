from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Drops the specified tables from the database'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            self.stdout.write('Dropping placementdb_companyinterview table...')
            try:
                cursor.execute("DROP TABLE placementdb_companyinterview")
                self.stdout.write(self.style.SUCCESS('Successfully dropped placementdb_companyinterview table.'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Could not drop placementdb_companyinterview table: {e}'))

            self.stdout.write('Dropping placementdrive_applyingrole table...')
            try:
                cursor.execute("DROP TABLE placementdrive_applyingrole")
                self.stdout.write(self.style.SUCCESS('Successfully dropped placementdrive_applyingrole table.'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Could not drop placementdrive_applyingrole table: {e}'))
from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Deletes migration records for specified apps from the django_migrations table'

    def handle(self, *args, **options):
        apps_to_clean = ['placementdb', 'placementdrive']
        with connection.cursor() as cursor:
            for app_name in apps_to_clean:
                self.stdout.write(f"Deleting migration records for {app_name}...")
                try:
                    cursor.execute("DELETE FROM django_migrations WHERE app = %s", [app_name])
                    self.stdout.write(self.style.SUCCESS(f'Successfully deleted migration records for {app_name}.'))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'Could not delete migration records for {app_name}: {e}'))

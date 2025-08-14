from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Drops the placementdb_companyinterview table'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            cursor.execute("DROP TABLE IF EXISTS placementdb_companyinterview")
        self.stdout.write(self.style.SUCCESS('Successfully dropped table "placementdb_companyinterview"'))
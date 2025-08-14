from django.core.management.base import BaseCommand
from django.db import connection

class Command(BaseCommand):
    help = 'Manually creates the placementdb_companyinterview table'

    def handle(self, *args, **options):
        with connection.cursor() as cursor:
            try:
                self.stdout.write("Creating placementdb_companyinterview table...")
                cursor.execute("""
                    CREATE TABLE "placementdb_companyinterview" (
                        "id" integer NOT NULL PRIMARY KEY AUTOINCREMENT,
                        "location" varchar(255) NULL,
                        "other_location" varchar(255) NULL,
                        "interview_date" date NOT NULL,
                        "interview_time" time NOT NULL,
                        "attended" bool NOT NULL,
                        "feedback" text NULL
                    );
                """)
                self.stdout.write(self.style.SUCCESS('Successfully created placementdb_companyinterview table.'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creating table: {e}'))

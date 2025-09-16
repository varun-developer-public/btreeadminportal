from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
import os
from unittest.mock import patch, MagicMock

from .models import DBBackupImport
from .db_utils import get_current_db_engine, import_sql_backup

User = get_user_model()

class DBBackupImportTest(TestCase):
    def setUp(self):
        # Create superuser
        self.superuser = User.objects.create_superuser(
            username='admin',
            email='admin@example.com',
            password='adminpassword'
        )
        
        # Create regular staff user
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='staffpassword',
            is_staff=True
        )
        
        # Create test client
        self.client = Client()
        
        # Create a test SQL file
        self.sql_content = "-- Test SQL file\nCREATE TABLE test_table (id INTEGER PRIMARY KEY, name TEXT);\nINSERT INTO test_table VALUES (1, 'Test');"
        self.test_sql_file = SimpleUploadedFile(
            "test_backup.sql",
            self.sql_content.encode('utf-8'),
            content_type="text/plain"
        )
    
    def test_access_control(self):
        """Test that only superusers can access the import DB backup page"""
        # Test unauthenticated access
        response = self.client.get(reverse('import_db_backup'))
        self.assertNotEqual(response.status_code, 200)
        
        # Test staff user access (should be denied)
        self.client.login(username='staff', password='staffpassword')
        response = self.client.get(reverse('import_db_backup'))
        self.assertNotEqual(response.status_code, 200)
        
        # Test superuser access (should be allowed)
        self.client.login(username='admin', password='adminpassword')
        response = self.client.get(reverse('import_db_backup'))
        self.assertEqual(response.status_code, 200)
    
    @patch('settingsdb.db_utils.get_current_db_engine')
    def test_db_engine_detection(self, mock_get_engine):
        """Test database engine detection"""
        # Test SQLite detection
        mock_get_engine.return_value = 'sqlite'
        self.assertEqual(get_current_db_engine(), 'sqlite')
        
        # Test PostgreSQL detection
        mock_get_engine.return_value = 'postgresql'
        self.assertEqual(get_current_db_engine(), 'postgresql')
        
        # Test MySQL detection
        mock_get_engine.return_value = 'mysql'
        self.assertEqual(get_current_db_engine(), 'mysql')
    
    @patch('settingsdb.db_utils.import_sql_backup')
    def test_sql_import_success(self, mock_import):
        """Test successful SQL import"""
        # Mock successful import
        mock_import.return_value = (True, "Import successful", ['test_table'])
        
        # Login as superuser
        self.client.login(username='admin', password='adminpassword')
        
        # Submit the form with a test SQL file
        response = self.client.post(
            reverse('import_db_backup'),
            {'uploaded_file': self.test_sql_file},
            follow=True
        )
        
        # Check that the import was successful
        self.assertContains(response, "Database backup imported successfully")
        
        # Check that a DBBackupImport record was created with the correct status
        self.assertEqual(DBBackupImport.objects.count(), 1)
        db_import = DBBackupImport.objects.first()
        self.assertEqual(db_import.status, 'COMPLETED')
        self.assertEqual(db_import.imported_by, self.superuser)
    
    @patch('settingsdb.db_utils.import_sql_backup')
    def test_sql_import_failure(self, mock_import):
        """Test failed SQL import"""
        # Mock failed import
        mock_import.return_value = (False, "Import failed: syntax error", [])
        
        # Login as superuser
        self.client.login(username='admin', password='adminpassword')
        
        # Submit the form with a test SQL file
        response = self.client.post(
            reverse('import_db_backup'),
            {'uploaded_file': self.test_sql_file},
            follow=True
        )
        
        # Check that the import failure message is displayed
        self.assertContains(response, "Error importing database backup")
        
        # Check that a DBBackupImport record was created with the correct status
        self.assertEqual(DBBackupImport.objects.count(), 1)
        db_import = DBBackupImport.objects.first()
        self.assertEqual(db_import.status, 'FAILED')
        self.assertEqual(db_import.error_message, "Import failed: syntax error")
    
    def test_file_validation(self):
        """Test file validation (only .sql files allowed)"""
        # Login as superuser
        self.client.login(username='admin', password='adminpassword')
        
        # Create an invalid file (not .sql)
        invalid_file = SimpleUploadedFile(
            "test_file.txt",
            b"This is not a SQL file",
            content_type="text/plain"
        )
        
        # Submit the form with an invalid file
        response = self.client.post(
            reverse('import_db_backup'),
            {'uploaded_file': invalid_file},
            follow=True
        )
        
        # Check that validation error is displayed
        self.assertContains(response, "File extension must be .sql")
        
        # Check that no DBBackupImport record was created
        self.assertEqual(DBBackupImport.objects.count(), 0)

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from datetime import datetime, timedelta
from .models import (
    Batch, BatchStudent, TransferRequest, 
    BatchTransaction, TrainerHandover
)
from studentsdb.models import Student
from trainersdb.models import Trainer
from coursedb.models import Course, CourseCategory

User = get_user_model()


class BatchModelTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            name='Test User',
            role='staff',
            password='testpassword'
        )
        
        self.category = CourseCategory.objects.create(name='Test Category')
        self.course = Course.objects.create(
            course_name='Test Course',
            category=self.category,
            total_duration=30,
            course_type='Course'
        )
        
        self.trainer = Trainer.objects.create(
            name='Test Trainer',
            email='trainer@example.com',
            phone_number='1234567890',
            employment_type='FT'
        )
        
        self.batch = Batch.objects.create(
            course=self.course,
            trainer=self.trainer,
            start_date=datetime.now().date(),
            end_date=(datetime.now() + timedelta(days=30)).date(),
            batch_type='WD',
            batch_status='YTS',
            start_time='09:00:00',
            end_time='11:00:00',
            days=['Monday', 'Wednesday', 'Friday'],
            created_by=self.user,
            updated_by=self.user
        )
        
        self.student = Student.objects.create(
            first_name='Test',
            last_name='Student',
            email='student@example.com',
            phone='9876543210'
        )
    
    def test_batch_id_generation(self):
        """Test that batch_id is generated correctly"""
        self.assertIsNotNone(self.batch.batch_id)
        expected_prefix = self.category.name[0].upper() + self.course.code[-2:].upper()
        self.assertTrue(self.batch.batch_id.startswith(expected_prefix))
        import re
        self.assertRegex(self.batch.batch_id, r'^[A-Z][A-Z0-9]{2}[A-Z]{2}$')
    
    def test_add_student(self):
        """Test adding a student to a batch"""
        # Initial count should be 0
        self.assertEqual(self.batch.batchstudent_set.count(), 0)
        
        # Add student
        batch_student = BatchStudent.objects.create(
            batch=self.batch,
            student=self.student
        )
        
        # Count should now be 1
        self.assertEqual(self.batch.batchstudent_set.count(), 1)
        self.assertTrue(batch_student.is_active)
        self.assertIsNotNone(batch_student.activated_at)
    
    def test_transaction_logging(self):
        """Test that transactions are logged when batch is updated"""
        # Initial transaction count
        initial_count = BatchTransaction.objects.filter(batch=self.batch).count()
        
        # Update batch
        self.batch.batch_status = 'ONGOING'
        self.batch.save(user=self.user)
        
        # Transaction count should increase
        new_count = BatchTransaction.objects.filter(batch=self.batch).count()
        self.assertEqual(new_count, initial_count + 1)


class TransferRequestTestCase(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            name='Test User',
            role='admin',
            password='testpassword'
        )
        
        self.category = CourseCategory.objects.create(name='Test Category')
        self.course = Course.objects.create(
            course_name='Test Course',
            category=self.category,
            total_duration=30,
            course_type='Course'
        )
        
        self.trainer = Trainer.objects.create(
            name='Test Trainer',
            email='trainer@example.com',
            phone_number='1234567890',
            employment_type='FT'
        )
        
        self.from_batch = Batch.objects.create(
            course=self.course,
            trainer=self.trainer,
            start_date=datetime.now().date(),
            end_date=(datetime.now() + timedelta(days=30)).date(),
            batch_type='WD',
            batch_status='IP',
            start_time='09:00:00',
            end_time='11:00:00',
            days=['Monday', 'Wednesday', 'Friday'],
            created_by=self.user,
            updated_by=self.user
        )
        
        self.to_batch = Batch.objects.create(
            course=self.course,
            trainer=self.trainer,
            start_date=datetime.now().date(),
            end_date=(datetime.now() + timedelta(days=30)).date(),
            batch_type='WD',
            batch_status='IP',
            start_time='14:00:00',
            end_time='16:00:00',
            days=['Tuesday', 'Thursday'],
            created_by=self.user,
            updated_by=self.user
        )
        
        self.student = Student.objects.create(
            first_name='Test',
            last_name='Student',
            email='student@example.com',
            phone='9876543210'
        )
        
        # Add student to from_batch
        self.batch_student = BatchStudent.objects.create(
            batch=self.from_batch,
            student=self.student
        )
    
    def test_transfer_request_creation(self):
        """Test creating a transfer request"""
        transfer_request = TransferRequest.objects.create(
            from_batch=self.from_batch,
            to_batch=self.to_batch,
            requested_by=self.user,
            remarks='Test transfer'
        )
        transfer_request.students.add(self.student)
        
        self.assertEqual(transfer_request.status, 'PENDING')
        self.assertEqual(transfer_request.students.count(), 1)
    
    def test_transfer_request_approval(self):
        """Test approving a transfer request"""
        transfer_request = TransferRequest.objects.create(
            from_batch=self.from_batch,
            to_batch=self.to_batch,
            requested_by=self.user,
            remarks='Test transfer'
        )
        transfer_request.students.add(self.student)
        
        # Approve the transfer request
        transfer_request.approve(self.user, [self.student])
        
        # Check status updated
        self.assertEqual(transfer_request.status, 'APPROVED')
        self.assertIsNotNone(transfer_request.approved_at)
        self.assertEqual(transfer_request.approved_by, self.user)
        
        # Check student moved to new batch
        self.assertFalse(BatchStudent.objects.filter(batch=self.from_batch, student=self.student, is_active=True).exists())
        self.assertTrue(BatchStudent.objects.filter(batch=self.to_batch, student=self.student, is_active=True).exists())

    def test_transfer_back_to_previous_batch(self):
        """Test transferring a student back to a previous batch and then away again"""
        # 1. Transfer from from_batch to to_batch
        tr1 = TransferRequest.objects.create(
            from_batch=self.from_batch,
            to_batch=self.to_batch,
            requested_by=self.user
        )
        tr1.students.add(self.student)
        tr1.approve(self.user, [self.student])
        
        # 2. Transfer from to_batch back to from_batch
        tr2 = TransferRequest.objects.create(
            from_batch=self.to_batch,
            to_batch=self.from_batch,
            requested_by=self.user
        )
        tr2.students.add(self.student)
        tr2.approve(self.user, [self.student])
        
        # At this point, from_batch has TWO BatchStudent records for this student:
        # one inactive (original) and one active (transferred back).
        self.assertEqual(BatchStudent.objects.filter(batch=self.from_batch, student=self.student).count(), 2)
        self.assertEqual(BatchStudent.objects.filter(batch=self.from_batch, student=self.student, is_active=True).count(), 1)
        
        # 3. Transfer from from_batch to to_batch AGAIN
        # This is where it failed before: BatchStudent.objects.get(batch=self.from_batch, student=student) matched 2 records.
        tr3 = TransferRequest.objects.create(
            from_batch=self.from_batch,
            to_batch=self.to_batch,
            requested_by=self.user
        )
        tr3.students.add(self.student)
        
        # This should NOT raise MultipleObjectsReturned
        tr3.approve(self.user, [self.student])
        
        self.assertEqual(transfer_request_status := tr3.status, 'APPROVED')
        self.assertFalse(BatchStudent.objects.filter(batch=self.from_batch, student=self.student, is_active=True).exists())
        self.assertTrue(BatchStudent.objects.filter(batch=self.to_batch, student=self.student, is_active=True).exists())



class BatchAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            name='Test User',
            role='admin',
            password='testpassword'
        )
        self.client.force_authenticate(user=self.user)
        
        self.category = CourseCategory.objects.create(name='Test Category')
        self.course = Course.objects.create(
            course_name='Test Course',
            category=self.category,
            total_duration=30,
            course_type='Course'
        )
        
        self.trainer = Trainer.objects.create(
            name='Test Trainer',
            email='trainer@example.com',
            phone_number='1234567890',
            employment_type='FT'
        )
        
        self.batch = Batch.objects.create(
            course=self.course,
            trainer=self.trainer,
            start_date=datetime.now().date(),
            end_date=(datetime.now() + timedelta(days=30)).date(),
            batch_type='WD',
            batch_status='YTS',
            start_time='09:00:00',
            end_time='11:00:00',
            days=['Monday', 'Wednesday', 'Friday'],
            created_by=self.user,
            updated_by=self.user
        )
        
        self.student = Student.objects.create(
            first_name='Test',
            last_name='Student',
            email='student@example.com',
            phone='9876543210'
        )
    
    def test_batch_list(self):
        """Test retrieving batch list"""
        url = reverse('batchdb_api:batch-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_batch_detail(self):
        """Test retrieving batch detail"""
        url = reverse('batchdb_api:batch-detail', args=[self.batch.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['batch_id'], self.batch.batch_id)
    
    def test_add_student_to_batch(self):
        """Test adding a student to a batch via API"""
        url = reverse('batchdb_api:batch-add-student', args=[self.batch.id])
        data = {'student_id': self.student.id}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(BatchStudent.objects.filter(batch=self.batch, student=self.student, is_active=True).exists())
    
    def test_student_batch_history(self):
        """Test retrieving student batch history"""
        # Add student to batch
        BatchStudent.objects.create(batch=self.batch, student=self.student)
        
        url = reverse('batchdb_api:studenthistory-list')
        response = self.client.get(url, {'student_id': self.student.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['student_id'], self.student.id)
        self.assertTrue(len(response.data['batch_history']) > 0)

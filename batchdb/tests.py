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
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        self.category = CourseCategory.objects.create(name='Test Category')
        self.course = Course.objects.create(
            name='Test Course',
            category=self.category,
            duration=30
        )
        
        self.trainer = Trainer.objects.create(
            name='Test Trainer',
            email='trainer@example.com',
            phone='1234567890'
        )
        
        self.batch = Batch.objects.create(
            course=self.course,
            trainer=self.trainer,
            start_date=datetime.now().date(),
            end_date=(datetime.now() + timedelta(days=30)).date(),
            batch_type='REGULAR',
            batch_status='UPCOMING',
            start_time='09:00:00',
            end_time='11:00:00',
            days='1,3,5',  # Monday, Wednesday, Friday
            created_by=self.user,
            updated_by=self.user
        )
        
        self.student = Student.objects.create(
            name='Test Student',
            email='student@example.com',
            phone='9876543210',
            enrollment_date=datetime.now().date()
        )
    
    def test_batch_id_generation(self):
        """Test that batch_id is generated correctly"""
        self.assertIsNotNone(self.batch.batch_id)
        self.assertTrue(self.batch.batch_id.startswith('B'))
    
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
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        
        self.category = CourseCategory.objects.create(name='Test Category')
        self.course = Course.objects.create(
            name='Test Course',
            category=self.category,
            duration=30
        )
        
        self.trainer = Trainer.objects.create(
            name='Test Trainer',
            email='trainer@example.com',
            phone='1234567890'
        )
        
        self.from_batch = Batch.objects.create(
            course=self.course,
            trainer=self.trainer,
            start_date=datetime.now().date(),
            end_date=(datetime.now() + timedelta(days=30)).date(),
            batch_type='REGULAR',
            batch_status='ONGOING',
            start_time='09:00:00',
            end_time='11:00:00',
            days='1,3,5',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.to_batch = Batch.objects.create(
            course=self.course,
            trainer=self.trainer,
            start_date=datetime.now().date(),
            end_date=(datetime.now() + timedelta(days=30)).date(),
            batch_type='REGULAR',
            batch_status='ONGOING',
            start_time='14:00:00',
            end_time='16:00:00',
            days='2,4',  # Tuesday, Thursday
            created_by=self.user,
            updated_by=self.user
        )
        
        self.student = Student.objects.create(
            name='Test Student',
            email='student@example.com',
            phone='9876543210',
            enrollment_date=datetime.now().date()
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
        self.assertFalse(BatchStudent.objects.get(batch=self.from_batch, student=self.student).is_active)
        self.assertTrue(BatchStudent.objects.filter(batch=self.to_batch, student=self.student, is_active=True).exists())


class BatchAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpassword'
        )
        self.client.force_authenticate(user=self.user)
        
        self.category = CourseCategory.objects.create(name='Test Category')
        self.course = Course.objects.create(
            name='Test Course',
            category=self.category,
            duration=30
        )
        
        self.trainer = Trainer.objects.create(
            name='Test Trainer',
            email='trainer@example.com',
            phone='1234567890'
        )
        
        self.batch = Batch.objects.create(
            course=self.course,
            trainer=self.trainer,
            start_date=datetime.now().date(),
            end_date=(datetime.now() + timedelta(days=30)).date(),
            batch_type='REGULAR',
            batch_status='UPCOMING',
            start_time='09:00:00',
            end_time='11:00:00',
            days='1,3,5',
            created_by=self.user,
            updated_by=self.user
        )
        
        self.student = Student.objects.create(
            name='Test Student',
            email='student@example.com',
            phone='9876543210',
            enrollment_date=datetime.now().date()
        )
    
    def test_batch_list(self):
        """Test retrieving batch list"""
        url = reverse('batchdb:batch-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_batch_detail(self):
        """Test retrieving batch detail"""
        url = reverse('batchdb:batch-detail', args=[self.batch.id])
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['batch_id'], self.batch.batch_id)
    
    def test_add_student_to_batch(self):
        """Test adding a student to a batch via API"""
        url = reverse('batchdb:batch-add-student', args=[self.batch.id])
        data = {'student_id': self.student.id}
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(BatchStudent.objects.filter(batch=self.batch, student=self.student, is_active=True).exists())
    
    def test_student_batch_history(self):
        """Test retrieving student batch history"""
        # Add student to batch
        BatchStudent.objects.create(batch=self.batch, student=self.student)
        
        url = reverse('batchdb:student-batch-history')
        response = self.client.get(url, {'student_id': self.student.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['student_id'], self.student.id)
        self.assertTrue(len(response.data['batch_history']) > 0)

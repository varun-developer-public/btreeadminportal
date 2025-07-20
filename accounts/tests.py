from django.test import TestCase, RequestFactory
from django.contrib.auth import get_user_model
from django.urls import reverse
from .middleware import RolePermissionsMiddleware

User = get_user_model()

class RolePermissionsMiddlewareTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = RolePermissionsMiddleware(get_response=lambda req: None)

        # Create users with different roles
        self.admin_user = User.objects.create_user(email='admin@test.com', name='Admin', role='admin', password='password')
        self.staff_user = User.objects.create_user(email='staff@test.com', name='Staff', role='staff', password='password')
        self.placement_user = User.objects.create_user(email='placement@test.com', name='Placement', role='placement', password='password')

    def test_staff_access(self):
        # Staff should have access to student list
        request = self.factory.get(reverse('student_list'))
        request.user = self.staff_user
        response = self.middleware(request)
        self.assertIsNone(response)

        # Staff should NOT have access to placement list
        request = self.factory.get(reverse('placement_list'))
        request.user = self.staff_user
        response = self.middleware(request)
        self.assertEqual(response.status_code, 403)

    def test_placement_access(self):
        # Placement should have access to placement list
        request = self.factory.get(reverse('placement_list'))
        request.user = self.placement_user
        response = self.middleware(request)
        self.assertIsNone(response)

        # Placement should NOT have access to student creation
        request = self.factory.get(reverse('create_student'))
        request.user = self.placement_user
        response = self.middleware(request)
        self.assertEqual(response.status_code, 403)

    def test_admin_access(self):
        # Admin should have access to everything
        request = self.factory.get(reverse('placement_list'))
        request.user = self.admin_user
        response = self.middleware(request)
        self.assertIsNone(response)

from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from django.db import models
from core.utils import profile_pics_upload_to

class CustomUserManager(BaseUserManager):
    def create_user(self, email, name, role, password=None, is_staff=False, is_superuser=False, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        if not name:
            raise ValueError("Users must have a name")
        if not role:
            raise ValueError("Users must have a role")

        email = self.normalize_email(email)
        user = self.model(email=email, name=name, role=role,
                          is_staff=is_staff, is_superuser=is_superuser, **extra_fields)
        user.set_password(password)
        user.save()
        return user

    def create_superuser(self, email, name, password=None, **extra_fields):
        return self.create_user(email, name, role='admin', password=password,
                                is_staff=True, is_superuser=True, **extra_fields)

class CustomUser(AbstractBaseUser, PermissionsMixin):

    ROLE_CHOICES = [
        ('admin', 'Admin'),
        ('staff', 'Staff'),
        ('placement', 'Placement'),
        ('trainer', 'Trainer'),
        ('student', 'Student'),
        ('batch_coordination', 'Batch Coordination'),
        ('consultant', 'Consultant'),
    ]

    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100)
    role = models.CharField(max_length=30, choices=ROLE_CHOICES)
    profile_picture = models.ImageField(upload_to=profile_pics_upload_to, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    totp_secret = models.CharField(max_length=100, blank=True, null=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name',]

    def __str__(self):
        return f"{self.email} ({self.role})"

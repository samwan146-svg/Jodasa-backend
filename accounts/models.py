from datetime import timedelta
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class School(models.Model):
    SUBSCRIPTION_CHOICES = [
        ('trial', 'Trial'),
        ('active', 'Active'),
        ('expired', 'Expired'),
    ]

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    county = models.CharField(max_length=100)

    subscription_status = models.CharField(
        max_length=10,
        choices=SUBSCRIPTION_CHOICES,
        default='trial'
    )
    trial_start_date = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    def is_trial_expired(self):
        return timezone.now() > self.trial_start_date + timedelta(days=14)
    def update_subscription_status(self):
        if self.subscription_status == 'trial' and self.is_trial_expired():
            self.subscription_status = 'expired'
            self.save()
    def __str__(self):
        return self.name


class Role(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name

class User(AbstractUser):
    username = models.CharField(max_length=150, unique=True)
    email = models.EmailField(unique=True)

    school = models.ForeignKey('School', on_delete=models.CASCADE, null=True, blank=True)
    role = models.ForeignKey('Role', on_delete=models.SET_NULL, null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    admission_number = models.CharField(max_length=50, unique=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True)
    grade = models.CharField(max_length=20, blank=True)
    stream = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"Student: {self.user.email}"


class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    staff_id = models.CharField(max_length=50, unique=True)
    subjects = models.TextField(blank=True)

    def __str__(self):
        return f"Teacher: {self.user.email}"

class AuditLog(models.Model):
    ACTION_CHOICES = [
        ('create_user', 'Create User'),
        ('update_role', 'Update Role'),
        ('delete_user', 'Delete User'),
    ]

    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    target_email = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(null=True, blank=True)  # 🔥 NEW
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.action} - {self.target_email}" 

class ParentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone_number = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"Parent: {self.user.email}"
# Create your models here.
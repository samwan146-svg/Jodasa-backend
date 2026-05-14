from datetime import timedelta
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from .managers import UserManager


class School(models.Model):
    SUBSCRIPTION_CHOICES = [
        ('trial', 'Trial'),
        ('active', 'Active'),
        ('expired', 'Expired'),
    ]

    name = models.CharField(max_length=255)
    code = models.CharField(max_length=50, unique=True)
    county = models.CharField(max_length=100)
    is_on_pilot = models.BooleanField(default=True)    
    logo = models.ImageField(upload_to='school_logos/', null=True, blank=True)
    
    # M-Pesa Credentials per School
    mpesa_shortcode = models.CharField(max_length=10, blank=True)
    mpesa_consumer_key = models.CharField(max_length=255, blank=True)
    mpesa_consumer_secret = models.CharField(max_length=255, blank=True)
    
    # CBC Preferences
    auto_generate_remarks = models.BooleanField(default=True)

    def get_days_remaining(self):
        if not self.trial_start_date:
           return 0
        expiry_date = self.trial_start_date + timedelta(days=60)
        remaining = (expiry_date - timezone.now()).days
        return max(0, remaining)

    subscription_status = models.CharField(
        max_length=10,
        choices=SUBSCRIPTION_CHOICES,
        default='trial'
    )
    trial_start_date = models.DateTimeField(default=timezone.now)
    is_active = models.BooleanField(default=True)
    def is_trial_expired(self):
        #Sync trial expiration with get_days_remaining
        return timezone.now() > self.trial_start_date + timedelta(days=60)
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
    email = models.EmailField(unique=True)
    school = models.ForeignKey('School', on_delete=models.CASCADE, null=True, blank=True)
    role = models.ForeignKey('Role', on_delete=models.SET_NULL, null=True, blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='students', null=True, blank=True) # Added null=True
    admission_number = models.CharField(max_length=50, unique=True)
    date_of_birth = models.DateField(null=True, blank=True)
    gender = models.CharField(max_length=10, blank=True)
    grade = models.CharField(max_length=20, blank=True)
    stream = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"Student: {self.user.email}"


class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='teachers', null=True, blank=True) # Added null=True
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

    school = models.ForeignKey(School, on_delete=models.CASCADE, null=True, blank=True) # Added null=True
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    target_email = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField(null=True, blank=True)  # 🔥 NEW
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user} - {self.action} - {self.target_email}" 

class ParentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='parents', null=True, blank=True)
    phone_number = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"Parent: {self.user.email}"

class Assessment(models.Model):
    TERM_CHOICES = [
        ('Term 1', 'Term 1'),
        ('Term 2', 'Term 2'),
        ('Term 3', 'Term 3'),
    ]

    school = models.ForeignKey(School, on_delete=models.CASCADE, null=True, blank=True) # Added null=True
    title = models.CharField(max_length=100)
    subject = models.CharField(max_length=50)
    grade = models.CharField(max_length=20)
    term = models.CharField(max_length=10, choices=TERM_CHOICES)
    max_marks = models.IntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.subject} ({self.grade})"


class StudentResult(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, null=True, blank=True) # Added null=True
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    assessment = models.ForeignKey(Assessment, on_delete=models.CASCADE)
    raw_score = models.DecimalField(max_digits=5, decimal_places=2)
    competency_level = models.CharField(max_length=50, blank=True)
    teacher_remarks = models.TextField(blank=True)
    date_recorded = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        percentage = (self.raw_score / self.assessment.max_marks) * 100
        if percentage >= 80:
            self.competency_level = 'Exceeding Expectation (EE)'
        elif percentage >= 50:
            self.competency_level = 'Meeting Expectation (ME)'
        elif percentage >= 30:
            self.competency_level = 'Approaching Expectation (AE)'
        else:
            self.competency_level = 'Below Expectation (BE)'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.student} - {self.assessment.title} - {self.competency_level}"

class FeeStructure(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, null=True, blank=True) # Added null=True
    grade = models.CharField(max_length=20)
    term = models.CharField(max_length=20, choices=[('Term 1', 'Term 1'), ('Term 2', 'Term 2'), ('Term 3', 'Term 3')])
    year = models.IntegerField(default=2026)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"{self.school.name} - {self.grade} ({self.term})"

class FeePayment(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, null=True, blank=True) # Added null=True
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    mpesa_receipt = models.CharField(max_length=100, unique=True, null=True, blank=True)
    description = models.CharField(max_length=255, default="School Fees Payment")
    timestamp = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20, 
        choices=[('Pending', 'Pending'), ('Completed', 'Completed'), ('Failed', 'Failed')],
        default='Pending'
    )
    checkout_request_id = models.CharField(max_length=100, blank=True, null=True) # To track the specific STK session

    def __str__(self):
        return f"{self.student.user.first_name} - {self.mpesa_receipt}"

class CBCEvidence(models.Model):
    COMPETENCY_CHOICES = [
        ('Communication', 'Communication and Collaboration'),
        ('Critical Thinking', 'Critical Thinking and Problem Solving'),
        ('Creativity', 'Creativity and Imagination'),
        ('Citizenship', 'Citizenship'),
        ('Learning to Learn', 'Learning to Learn'),
        ('Self-Efficacy', 'Self-Efficacy'),
        ('Digital Literacy', 'Digital Literacy'),
    ]

    school = models.ForeignKey(School, on_delete=models.CASCADE)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='evidence_gallery')
    subject = models.CharField(max_length=50)
    competency_tagged = models.CharField(max_length=50, choices=COMPETENCY_CHOICES)
    evidence_image = models.ImageField(upload_to='cbc_evidence/')
    teacher_notes = models.TextField(blank=True)
    date_uploaded = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Evidence: {self.student.user.first_name} - {self.competency_tagged}"        
# Create your models here.
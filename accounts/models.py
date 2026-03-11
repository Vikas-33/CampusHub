from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ('college', 'College Admin'),
        ('teacher', 'Teacher'),
        ('student', 'Student'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    phone = models.CharField(max_length=15, blank=True)
    profile_pic = models.ImageField(upload_to='profiles/', blank=True, null=True)
    
    def is_college(self):
        return self.role == 'college'
    def is_teacher(self):
        return self.role == 'teacher'
    def is_student(self):
        return self.role == 'student'

class CollegeProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='college_profile')
    college_name = models.CharField(max_length=200)
    address = models.TextField()
    established_year = models.IntegerField(null=True, blank=True)
    website = models.URLField(blank=True)
    accreditation = models.CharField(max_length=100, blank=True)
    total_departments = models.IntegerField(default=0)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.college_name

class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    college = models.ForeignKey(CollegeProfile, on_delete=models.CASCADE, related_name='teachers')
    employee_id = models.CharField(max_length=50, unique=True)
    department = models.CharField(max_length=100)
    designation = models.CharField(max_length=100)
    qualification = models.CharField(max_length=200)
    joining_date = models.DateField(null=True, blank=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    specialization = models.CharField(max_length=200, blank=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.department}"

class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    college = models.ForeignKey(CollegeProfile, on_delete=models.CASCADE, related_name='students')
    roll_number = models.CharField(max_length=50)
    enrollment_number = models.CharField(max_length=50, unique=True)

    # Changed from CharField to ForeignKey to match Course.department
    department = models.ForeignKey(
        'academics.Department',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='students'
    )

    semester = models.IntegerField(default=1)
    batch_year = models.IntegerField()
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    guardian_name = models.CharField(max_length=100, blank=True)
    guardian_phone = models.CharField(max_length=15, blank=True)
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.roll_number}"
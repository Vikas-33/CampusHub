from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    ROLE_CHOICES = [('college', 'College'), ('teacher', 'Teacher'), ('student', 'Student')]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    phone = models.CharField(max_length=15, blank=True)
    profile_pic = models.ImageField(upload_to='profiles/', blank=True, null=True)

    def is_college(self): return self.role == 'college'
    def is_teacher(self): return self.role == 'teacher'
    def is_student(self): return self.role == 'student'

    def __str__(self): return f"{self.username} ({self.role})"


class CollegeProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='college_profile')
    college_id = models.CharField(max_length=20, unique=True, blank=True)
    slug = models.SlugField(max_length=20, unique=True, blank=True,
                            help_text='Short code for URL e.g. ACE, NIT, DIT')
    college_name = models.CharField(max_length=200)
    address = models.TextField(blank=True)
    established_year = models.IntegerField(null=True, blank=True)
    website = models.URLField(blank=True)
    phone = models.CharField(max_length=15, blank=True)

    def _generate_college_id(self):
        last = CollegeProfile.objects.filter(
            college_id__startswith='CLG'
        ).order_by('-college_id').first()
        if last and last.college_id:
            try:
                num = int(last.college_id[3:]) + 1
            except ValueError:
                num = 1
        else:
            num = 1
        return f"CLG{num:05d}"

    def get_initials(self):
        words = self.college_name.upper().split()
        return ''.join(w[0] for w in words if w)[:3]

    def save(self, *args, **kwargs):
        if not self.college_id:
            self.college_id = self._generate_college_id()
        # Auto-generate slug from initials if not set
        if not self.slug:
            self.slug = self.get_initials()
        super().save(*args, **kwargs)
        if self.user.username != self.college_id:
            self.user.username = self.college_id
            self.user.save(update_fields=['username'])

    def __str__(self): return self.college_name


class TeacherProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='teacher_profile')
    college = models.ForeignKey(CollegeProfile, on_delete=models.CASCADE, related_name='teachers')
    employee_id = models.CharField(max_length=20, unique=True, blank=True)
    department = models.CharField(max_length=100, blank=True)
    designation = models.CharField(max_length=100, blank=True)
    qualification = models.CharField(max_length=200, blank=True)
    joining_date = models.DateField(null=True, blank=True)
    salary = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    specialization = models.CharField(max_length=200, blank=True)

    def _generate_employee_id(self):
        initials = self.college.get_initials()
        count = TeacherProfile.objects.filter(college=self.college).count() + 1
        return f"{initials}-T-{count:04d}"

    def save(self, *args, **kwargs):
        if not self.employee_id:
            self.employee_id = self._generate_employee_id()
        super().save(*args, **kwargs)
        # if self.user.username != self.employee_id:
        #     self.user.username = self.employee_id
        #     self.user.save(update_fields=['username'])

    def __str__(self): return f"{self.user.get_full_name()} ({self.employee_id})"


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    college = models.ForeignKey(CollegeProfile, on_delete=models.CASCADE, related_name='students')
    roll_number = models.CharField(max_length=20, unique=True, blank=True)
    enrollment_number = models.CharField(max_length=50, unique=True, blank=True)
    department = models.ForeignKey('academics.Department', on_delete=models.SET_NULL, null=True, blank=True, related_name='students')
    semester = models.IntegerField(default=1)
    batch_year = models.IntegerField(null=True, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    address = models.TextField(blank=True)
    guardian_name = models.CharField(max_length=100, blank=True)
    guardian_phone = models.CharField(max_length=15, blank=True)

    def _generate_student_ids(self):
        from datetime import date
        year = self.batch_year or date.today().year
        if self.department:
            dept_code = (getattr(self.department, 'code', None) or self.department.name[:4]).upper()
        else:
            dept_code = 'GEN'
        initials = self.college.get_initials()
        dept_count = StudentProfile.objects.filter(
            college=self.college, department=self.department, batch_year=year
        ).count() + 1
        total_count = StudentProfile.objects.filter(college=self.college).count() + 1
        roll_number = f"{initials}{dept_code}{year}{dept_count:03d}" 
        enrollment_number = f"{initials}{year}S{total_count:04d}"
        return roll_number, enrollment_number

    def save(self, *args, **kwargs):
        if not self.roll_number or not self.enrollment_number:
            roll, enroll = self._generate_student_ids()
            if not self.roll_number:
                self.roll_number = roll
            if not self.enrollment_number:
                self.enrollment_number = enroll
        super().save(*args, **kwargs)
        # if self.user.username != self.roll_number:
        #     self.user.username = self.roll_number
        #     self.user.save(update_fields=['username'])

    def __str__(self): return f"{self.user.get_full_name()} ({self.roll_number})"
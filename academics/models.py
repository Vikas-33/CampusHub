from django.db import models
from accounts.models import CollegeProfile, TeacherProfile, StudentProfile

class Department(models.Model):
    college = models.ForeignKey(CollegeProfile, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20)
    head_of_department = models.ForeignKey(TeacherProfile, null=True, blank=True, on_delete=models.SET_NULL, related_name='headed_departments')
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - ({self.code})"

class Course(models.Model):
    college = models.ForeignKey(CollegeProfile, on_delete=models.CASCADE, related_name='courses')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, related_name='courses')
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20)
    credits = models.IntegerField(default=3)
    semester = models.IntegerField()
    teacher = models.ForeignKey(TeacherProfile, null=True, blank=True, on_delete=models.SET_NULL, related_name='teaching_courses')
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.code} - {self.name}"

class Attendance(models.Model):
    STATUS_CHOICES = [('present', 'Present'), ('absent', 'Absent'), ('late', 'Late')]
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='attendances')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='present')
    marked_by = models.ForeignKey(TeacherProfile, null=True, on_delete=models.SET_NULL)
    remarks = models.CharField(max_length=200, blank=True)
    
    class Meta:
        unique_together = ('course', 'student', 'date')
    
    def __str__(self):
        return f"{self.student} - {self.course} - {self.date}"

class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='assignments')
    title = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateTimeField()
    total_marks = models.IntegerField(default=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.course.name}"

class AssignmentSubmission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE, related_name='submissions')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='submissions')
    submitted_at = models.DateTimeField(auto_now_add=True)
    file = models.FileField(upload_to='assignments/', blank=True, null=True)
    remarks = models.TextField(blank=True)
    marks_obtained = models.IntegerField(null=True, blank=True)
    graded_by = models.ForeignKey(TeacherProfile, null=True, blank=True, on_delete=models.SET_NULL)
    
    class Meta:
        unique_together = ('assignment', 'student')

class Exam(models.Model):
    EXAM_TYPES = [('midterm', 'Midterm'), ('final', 'Final'), ('quiz', 'Quiz'), ('practical', 'Practical')]
    college = models.ForeignKey(CollegeProfile, on_delete=models.CASCADE, related_name='exams')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='exams')
    exam_type = models.CharField(max_length=20, choices=EXAM_TYPES)
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    total_marks = models.IntegerField(default=100)
    passing_marks = models.IntegerField(default=40)
    venue = models.CharField(max_length=100, blank=True)

    SEMESTER_CHOICES = [(str(i), f'Semester {i}') for i in range(1, 9)]
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('cancelled', 'Cancelled'),
        ('postponed', 'Postponed'),
    ]
    semester = models.CharField(max_length=1, choices=SEMESTER_CHOICES, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='scheduled')
    postponed_date = models.DateField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.course.name} - {self.exam_type} - {self.date}"

class ExamResult(models.Model):
    GRADE_CHOICES = [('A+','A+'),('A','A'),('B+','B+'),('B','B'),('C','C'),('D','D'),('F','F')]
    exam = models.ForeignKey(Exam, on_delete=models.CASCADE, related_name='results')
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='results')
    marks_obtained = models.IntegerField()
    grade = models.CharField(max_length=3, choices=GRADE_CHOICES, blank=True)
    remarks = models.TextField(blank=True)
    
    class Meta:
        unique_together = ('exam', 'student')

class Notice(models.Model):
    NOTICE_TYPES = [('general','General'),('academic','Academic'),('exam','Exam'),('event','Event'),('urgent','Urgent')]
    TARGET_CHOICES = [('all','All'),('students','Students Only'),('teachers','Teachers Only')]
    college = models.ForeignKey(CollegeProfile, on_delete=models.CASCADE, related_name='notices')
    title = models.CharField(max_length=200)
    content = models.TextField()
    notice_type = models.CharField(max_length=20, choices=NOTICE_TYPES, default='general')
    target_audience = models.CharField(max_length=20, choices=TARGET_CHOICES, default='all')
    created_by = models.ForeignKey('accounts.User', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    read_by = models.ManyToManyField('accounts.User', blank=True, related_name='read_notices')

    def __str__(self):
        return self.title

class FeeStructure(models.Model):
    college = models.ForeignKey(CollegeProfile, on_delete=models.CASCADE, related_name='fee_structures')
    name = models.CharField(max_length=100)
    department = models.CharField(max_length=100, blank=True)
    semester = models.IntegerField(null=True, blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    due_date = models.DateField(null=True, blank=True)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.name} - {self.amount}"

class FeePayment(models.Model):
    STATUS_CHOICES = [('pending','Pending'),('paid','Paid'),('overdue','Overdue'),('partial','Partial'),('overpaid', 'Overpaid'),]
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='fee_payments')
    fee_structure = models.ForeignKey(FeeStructure, on_delete=models.CASCADE)
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    transaction_id = models.CharField(max_length=100, blank=True)
    receipt_number = models.CharField(max_length=50, blank=True)
    remarks = models.CharField(max_length=200, blank=True)
    
    def __str__(self):
        return f"{self.student} - {self.fee_structure.name} - {self.status}"

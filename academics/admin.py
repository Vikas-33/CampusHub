from django.contrib import admin
from .models import Department, Course, Attendance, Assignment, AssignmentSubmission, Exam, ExamResult, Notice, FeeStructure, FeePayment

admin.site.register(Department)
admin.site.register(Course)
admin.site.register(Attendance)
admin.site.register(Assignment)
admin.site.register(Exam)
admin.site.register(ExamResult)
admin.site.register(Notice)
admin.site.register(FeeStructure)
admin.site.register(FeePayment)

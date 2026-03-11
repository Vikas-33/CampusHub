from django.urls import path
from . import views

urlpatterns = [
    path('departments/', views.departments, name='departments'),
    path('departments/add/', views.add_department, name='add_department'),
    path('courses/', views.courses, name='courses'),
    path('courses/add/', views.add_course, name='add_course'),
    path('attendance/', views.attendance, name='attendance'),
    path('attendance/mark/<int:course_id>/', views.mark_attendance, name='mark_attendance'),
    path('attendance/export/student/', views.export_attendance_student, name='export_attendance_student'),
    path('attendance/export/teacher/<int:course_id>/', views.export_attendance_teacher, name='export_attendance_teacher'),
    path('assignments/', views.assignments, name='assignments'),
    path('assignments/add/', views.add_assignment, name='add_assignment'),
    path('assignments/<int:pk>/submit/', views.submit_assignment, name='submit_assignment'),
    path('assignments/<int:pk>/grade/', views.grade_submissions, name='grade_submissions'),
    path('exams/', views.exams, name='exams'),
    path('exams/add/', views.add_exam, name='add_exam'),
    path('exams/<int:exam_id>/results/', views.exam_results, name='exam_results'),
    path('results/', views.student_results, name='student_results'),
    path('results/<int:exam_id>/', views.student_exam_result, name='student_exam_result'),
    path('notices/', views.notices, name='notices'),
    path('notices/add/', views.add_notice, name='add_notice'),
    path('notices/<int:pk>/edit/', views.edit_notice, name='edit_notice'),
    path('notices/<int:pk>/delete/', views.delete_notice, name='delete_notice'),
    path('fees/', views.fees, name='fees'),
    path('fees/structure/add/', views.add_fee_structure, name='add_fee_structure'),
    path('fees/payment/record/', views.record_payment, name='record_payment'),
    path('fees/receipt/<int:payment_id>/', views.download_fee_receipt, name='download_fee_receipt'),

]
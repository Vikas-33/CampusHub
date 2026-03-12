from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Count
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from .models import Department, Course, Attendance, Assignment, AssignmentSubmission, Exam, ExamResult, Notice, FeeStructure, FeePayment
from .forms import DepartmentForm, CourseForm, AttendanceForm, AssignmentForm, AssignmentSubmissionForm, ExamForm, ExamResultForm, NoticeForm, FeeStructureForm, FeePaymentForm
from .utils import send_notice_email, send_assignment_email, send_result_email
from accounts.models import StudentProfile, TeacherProfile
import csv


# --- DEPARTMENTS ---

@login_required
def departments(request, college_slug):
    if not request.user.is_college():
        return redirect('dashboard', college_slug=college_slug)
    college = request.user.college_profile
    depts = Department.objects.filter(college=college).annotate(
        course_count=Count('courses')
    )
    return render(request, 'academics/departments.html', {'departments': depts})


@login_required
def add_department(request, college_slug):
    if not request.user.is_college():
        return redirect('dashboard', college_slug=college_slug)
    college = request.user.college_profile
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        form.fields['head_of_department'].queryset = TeacherProfile.objects.filter(college=college)
        if form.is_valid():
            dept = form.save(commit=False)
            dept.college = college
            dept.save()
            messages.success(request, 'Department added!')
            return redirect('departments', college_slug=college_slug)
    else:
        form = DepartmentForm()
        form.fields['head_of_department'].queryset = TeacherProfile.objects.filter(college=college)
    return render(request, 'academics/add_department.html', {'form': form})


# --- COURSES ---

@login_required
def courses(request, college_slug):
    user = request.user
    if user.is_college():
        college = user.college_profile
        course_list = Course.objects.filter(college=college).select_related('teacher__user', 'department')
    elif user.is_teacher():
        course_list = Course.objects.filter(teacher=user.teacher_profile).select_related('department')
        college = user.teacher_profile.college
    else:
        student = user.student_profile
        course_list = Course.objects.filter(
            college=student.college,
            department=student.department,
            semester=student.semester
        )
        college = student.college
    return render(request, 'academics/courses.html', {'courses': course_list})


@login_required
def add_course(request, college_slug):
    if not request.user.is_college():
        return redirect('dashboard', college_slug=college_slug)
    college = request.user.college_profile
    if request.method == 'POST':
        form = CourseForm(request.POST)
        form.fields['department'].queryset = Department.objects.filter(college=college)
        form.fields['teacher'].queryset = TeacherProfile.objects.filter(college=college)
        if form.is_valid():
            course = form.save(commit=False)
            course.college = college
            course.save()
            messages.success(request, 'Course added!')
            return redirect('courses', college_slug=college_slug)
    else:
        form = CourseForm()
        form.fields['department'].queryset = Department.objects.filter(college=college)
        form.fields['teacher'].queryset = TeacherProfile.objects.filter(college=college)
    return render(request, 'academics/add_course.html', {'form': form})


# --- ATTENDANCE ---

@login_required
def attendance(request, college_slug):
    user = request.user
    if user.is_teacher():
        teacher = user.teacher_profile
        courses = Course.objects.filter(teacher=teacher)
        course_id = request.GET.get('course')
        selected_course = None
        attendance_records = []
        if course_id:
            selected_course = get_object_or_404(Course, pk=course_id, teacher=teacher)
            attendance_records = Attendance.objects.filter(
                course=selected_course
            ).select_related('student__user').order_by('-date')
        return render(request, 'academics/attendance_teacher.html', {
            'courses': courses,
            'selected_course': selected_course,
            'attendance_records': attendance_records
        })
    elif user.is_student():
        student = user.student_profile
        attendance_records = Attendance.objects.filter(
            student=student
        ).select_related('course').order_by('-date')
        total = attendance_records.count()
        present = attendance_records.filter(status='present').count()
        percent = round((present / total * 100), 1) if total > 0 else 0
        return render(request, 'academics/attendance_student.html', {
            'attendance_records': attendance_records,
            'total': total,
            'present': present,
            'percent': percent
        })
    else:
        college = user.college_profile
        attendance_records = Attendance.objects.filter(
            course__college=college
        ).select_related('student__user', 'course').order_by('-date')[:50]
        return render(request, 'academics/attendance_college.html', {
            'attendance_records': attendance_records
        })


@login_required
def mark_attendance(request, college_slug, course_id):
    if not request.user.is_teacher():
        return redirect('dashboard', college_slug=college_slug)
    teacher = request.user.teacher_profile
    course = get_object_or_404(Course, pk=course_id, teacher=teacher)
    students = StudentProfile.objects.filter(
        college=teacher.college,
        department=course.department,
        semester=course.semester
    )
    if request.method == 'POST':
        date = request.POST.get('date')
        for student in students:
            status = request.POST.get(f'status_{student.id}', 'absent')
            Attendance.objects.update_or_create(
                course=course, student=student, date=date,
                defaults={'status': status, 'marked_by': teacher}
            )
        messages.success(request, 'Attendance marked!')
        return redirect('attendance', college_slug=college_slug)
    from datetime import date as d
    return render(request, 'academics/mark_attendance.html', {
        'course': course, 'students': students, 'today': d.today()
    })


@login_required
def export_attendance_student(request, college_slug):
    if not request.user.is_student():
        return redirect('dashboard', college_slug=college_slug)
    student = request.user.student_profile
    records = Attendance.objects.filter(
        student=student
    ).select_related('course').order_by('course__name', 'date')

    course_stats = {}
    for rec in records:
        cname = rec.course.name
        if cname not in course_stats:
            course_stats[cname] = {'total': 0, 'present': 0}
        course_stats[cname]['total'] += 1
        if rec.status == 'present':
            course_stats[cname]['present'] += 1

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="attendance_{student.roll_number}.csv"'
    writer = csv.writer(response)
    writer.writerow(['ATTENDANCE REPORT'])
    writer.writerow(['Student', student.user.get_full_name()])
    writer.writerow(['Roll Number', student.roll_number])
    writer.writerow(['Enrollment No.', student.enrollment_number])
    writer.writerow(['Department', str(student.department) if student.department else ''])
    writer.writerow(['Semester', student.semester])
    writer.writerow([])
    writer.writerow(['COURSE-WISE SUMMARY'])
    writer.writerow(['Course', 'Total Classes', 'Present', 'Absent', 'Percentage'])
    for course_name, stats in course_stats.items():
        absent = stats['total'] - stats['present']
        pct = round(stats['present'] / stats['total'] * 100, 1) if stats['total'] > 0 else 0
        writer.writerow([course_name, stats['total'], stats['present'], absent, f"{pct}%"])
    writer.writerow([])
    writer.writerow(['DETAILED RECORDS'])
    writer.writerow(['Course', 'Date', 'Status'])
    for rec in records:
        writer.writerow([rec.course.name, rec.date.strftime('%d %b %Y'), rec.status.capitalize()])
    return response


@login_required
def export_attendance_teacher(request, college_slug, course_id):
    if not request.user.is_teacher():
        return redirect('dashboard', college_slug=college_slug)
    teacher = request.user.teacher_profile
    course = get_object_or_404(Course, pk=course_id, teacher=teacher)
    records = Attendance.objects.filter(
        course=course
    ).select_related('student__user').order_by('student__user__first_name', 'date')

    student_stats = {}
    for rec in records:
        sid = rec.student.pk
        if sid not in student_stats:
            student_stats[sid] = {
                'name': rec.student.user.get_full_name(),
                'roll': rec.student.roll_number,
                'total': 0, 'present': 0
            }
        student_stats[sid]['total'] += 1
        if rec.status == 'present':
            student_stats[sid]['present'] += 1

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="attendance_{course.code}.csv"'
    writer = csv.writer(response)
    writer.writerow(['ATTENDANCE REPORT'])
    writer.writerow(['Course', course.name])
    writer.writerow(['Course Code', course.code])
    writer.writerow(['Semester', course.semester])
    writer.writerow(['Teacher', teacher.user.get_full_name()])
    writer.writerow([])
    writer.writerow(['STUDENT-WISE SUMMARY'])
    writer.writerow(['Student Name', 'Roll Number', 'Total Classes', 'Present', 'Absent', 'Percentage'])
    for sid, stats in student_stats.items():
        absent = stats['total'] - stats['present']
        pct = round(stats['present'] / stats['total'] * 100, 1) if stats['total'] > 0 else 0
        writer.writerow([stats['name'], stats['roll'], stats['total'], stats['present'], absent, f"{pct}%"])
    writer.writerow([])
    writer.writerow(['DETAILED RECORDS'])
    writer.writerow(['Student', 'Roll Number', 'Date', 'Status'])
    for rec in records:
        writer.writerow([
            rec.student.user.get_full_name(),
            rec.student.roll_number,
            rec.date.strftime('%d %b %Y'),
            rec.status.capitalize()
        ])
    return response


# --- ASSIGNMENTS --- 

@login_required
def assignments(request, college_slug):
    user = request.user
    if user.is_teacher():
        assignment_list = Assignment.objects.filter(
            course__teacher=user.teacher_profile
        ).select_related('course').annotate(
            submission_count=Count('submissions')
        ).order_by('-created_at')
        now = timezone.now()
        for a in assignment_list:
            a.is_overdue = a.due_date < now
        paginator = Paginator(assignment_list, 15)
        page_obj = paginator.get_page(request.GET.get('page'))
        return render(request, 'academics/assignments.html', {'page_obj': page_obj})

    elif user.is_student():
        student = user.student_profile
        courses = Course.objects.filter(
            college=student.college,
            department=student.department,
            semester=student.semester
        )
        assignment_list = Assignment.objects.filter(
            course__in=courses
        ).select_related('course').order_by('-created_at')
        submissions = AssignmentSubmission.objects.filter(
            student=student, assignment__in=assignment_list
        )
        submitted_ids = set(submissions.values_list('assignment_id', flat=True))
        now = timezone.now()
        for a in assignment_list:
            a.is_overdue = a.due_date < now
        paginator = Paginator(assignment_list, 15)
        page_obj = paginator.get_page(request.GET.get('page'))
        return render(request, 'academics/assignments.html', {
            'page_obj': page_obj,
            'submissions': submissions,
            'submitted_ids': submitted_ids,
        })

    else:
        college = user.college_profile
        assignment_list = Assignment.objects.filter(
            course__college=college
        ).select_related('course').annotate(
            submission_count=Count('submissions')
        ).order_by('-created_at')
        now = timezone.now()
        for a in assignment_list:
            a.is_overdue = a.due_date < now
        paginator = Paginator(assignment_list, 15)
        page_obj = paginator.get_page(request.GET.get('page'))
        return render(request, 'academics/assignments.html', {'page_obj': page_obj})


@login_required
def add_assignment(request, college_slug):
    if not request.user.is_teacher():
        return redirect('dashboard', college_slug=college_slug)
    teacher = request.user.teacher_profile
    if request.method == 'POST':
        form = AssignmentForm(request.POST)
        form.fields['course'].queryset = Course.objects.filter(teacher=teacher)
        if form.is_valid():
            assignment = form.save()
            send_assignment_email(assignment)
            messages.success(request, 'Assignment created! Students will be notified by email.')
            return redirect('assignments', college_slug=college_slug)
    else:
        form = AssignmentForm()
        form.fields['course'].queryset = Course.objects.filter(teacher=teacher)
    return render(request, 'academics/add_assignment.html', {'form': form})


@login_required
def submit_assignment(request, college_slug, pk):
    if not request.user.is_student():
        return redirect('dashboard', college_slug=college_slug)
    assignment = get_object_or_404(Assignment, pk=pk)
    student = request.user.student_profile
    already_submitted = AssignmentSubmission.objects.filter(
        assignment=assignment, student=student
    ).exists()
    if already_submitted:
        messages.warning(request, 'You have already submitted this assignment.')
        return redirect('assignments', college_slug=college_slug)
    if request.method == 'POST':
        form = AssignmentSubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            sub = form.save(commit=False)
            sub.assignment = assignment
            sub.student = student
            sub.save()
            messages.success(request, 'Assignment submitted!')
            return redirect('assignments', college_slug=college_slug)
    else:
        form = AssignmentSubmissionForm()
    return render(request, 'academics/submit_assignment.html', {
        'form': form, 'assignment': assignment
    })


@login_required
def grade_submissions(request, college_slug, pk):
    if not request.user.is_teacher():
        return redirect('dashboard', college_slug=college_slug)
    assignment = get_object_or_404(Assignment, pk=pk, course__teacher=request.user.teacher_profile)
    submissions = AssignmentSubmission.objects.filter(
        assignment=assignment
    ).select_related('student__user')
    if request.method == 'POST':
        for sub in submissions:
            marks = request.POST.get(f'marks_{sub.id}')
            if marks:
                sub.marks_obtained = int(marks)
                sub.graded_by = request.user.teacher_profile
                sub.save()
        messages.success(request, 'Grades saved!')
        return redirect('assignments', college_slug=college_slug)
    return render(request, 'academics/grade_submissions.html', {
        'assignment': assignment, 'submissions': submissions
    })


# --- EXAMS ---

@login_required
def exams(request, college_slug):
    user = request.user
    if user.is_college():
        exam_list = Exam.objects.filter(
            college=user.college_profile
        ).select_related('course').order_by('date')
    elif user.is_teacher():
        exam_list = Exam.objects.filter(
            course__teacher=user.teacher_profile
        ).select_related('course').order_by('date')
    else:
        student = user.student_profile
        courses = Course.objects.filter(
            college=student.college,
            department=student.department,
            semester=student.semester
        )
        if courses.exists():
            exam_list = Exam.objects.filter(
                course__in=courses
            ).select_related('course').order_by('date')
        else:
            exam_list = Exam.objects.filter(
                college=student.college
            ).select_related('course').order_by('date')
    return render(request, 'academics/exams.html', {'exams': exam_list})


@login_required
def add_exam(request, college_slug):
    if not (request.user.is_college() or request.user.is_teacher()):
        return redirect('dashboard', college_slug=college_slug)
    if request.user.is_college():
        college = request.user.college_profile
        course_qs = Course.objects.filter(college=college)
    else:
        teacher = request.user.teacher_profile
        college = teacher.college
        course_qs = Course.objects.filter(teacher=teacher)
    SEMESTER_CHOICES = [(str(i), f'Semester {i}') for i in range(1, 9)]
    if request.method == 'POST':
        course_id     = request.POST.get('course')
        exam_type     = request.POST.get('exam_type')
        date          = request.POST.get('date')
        venue         = request.POST.get('venue', '')
        start_time    = request.POST.get('start_time')
        end_time      = request.POST.get('end_time')
        total_marks   = request.POST.get('total_marks', 100)
        passing_marks = request.POST.get('passing_marks', 40)
        semester      = request.POST.get('semester', '')
        course = get_object_or_404(Course, pk=course_id)
        exam = Exam.objects.create(
            college=college, course=course, exam_type=exam_type,
            date=date, venue=venue, start_time=start_time, end_time=end_time,
            total_marks=total_marks, passing_marks=passing_marks,
            semester=semester, status='scheduled',
        )
        # email students matching semester + course department
        students = StudentProfile.objects.filter(
            college=college,
            department=course.department,
            semester=int(semester) if semester else course.semester
        )
        emails = [s.user.email for s in students if s.user.email]
        if emails:
            from django.core.mail import send_mail
            from django.conf import settings
            send_mail(
                f"Exam Scheduled: {course.name} — {exam.get_exam_type_display()}",
                f"Dear Student,\n\nAn exam has been scheduled:\n\n"
                f"Course : {course.name}\nType   : {exam.get_exam_type_display()}\n"
                f"Date     : {exam.date}\n"
                f"Time   : {exam.start_time} – {exam.end_time}\n"
                f"Venue  : {venue or 'TBA'}\n\nAll the best!\n— CampusHub",
                settings.EMAIL_HOST_USER, emails, fail_silently=True
            )
        messages.success(request, 'Exam scheduled!')
        return redirect('exams', college_slug=college_slug)
    return render(request, 'academics/add_exam.html', {
        'courses': course_qs,
        'semester_choices': SEMESTER_CHOICES,
        'college_slug': college_slug,
    })



@login_required
def exam_results(request, college_slug, exam_id):
    if request.user.is_student():
        return redirect('student_exam_result', college_slug=college_slug, exam_id=exam_id)
    exam = get_object_or_404(Exam, pk=exam_id)
    results = ExamResult.objects.filter(exam=exam).select_related('student__user')
    if request.method == 'POST':
        student_id = request.POST.get('student_id')
        marks = request.POST.get('marks')
        grade = request.POST.get('grade')
        student = get_object_or_404(StudentProfile, pk=student_id)
        result, created = ExamResult.objects.update_or_create(
            exam=exam, student=student,
            defaults={'marks_obtained': int(marks), 'grade': grade}
        )
        send_result_email(result)
        messages.success(request, f'Result saved! {student.user.get_full_name()} will be notified by email.')
        return redirect('exam_results', college_slug=college_slug, exam_id=exam_id)
    students = StudentProfile.objects.filter(
        college=exam.college,
        department=exam.course.department,
        semester=exam.course.semester
    )
    return render(request, 'academics/exam_results.html', {
        'exam': exam, 'results': results, 'students': students
    })


# --- STUDENT RESULTS ---

@login_required
def student_results(request, college_slug):
    if not request.user.is_student():
        return redirect('dashboard', college_slug=college_slug)
    student = request.user.student_profile
    results = ExamResult.objects.filter(
        student=student
    ).select_related('exam__course').order_by('-exam__date')
    total_exams = results.count()
    passed = sum(1 for r in results if r.marks_obtained >= r.exam.passing_marks)
    failed = total_exams - passed
    average = round(
        sum((r.marks_obtained / r.exam.total_marks * 100) for r in results) / total_exams, 1
    ) if total_exams > 0 else 0
    return render(request, 'academics/student_results.html', {
        'student': student,
        'results': results,
        'total_exams': total_exams,
        'passed': passed,
        'failed': failed,
        'average': average,
    })


@login_required
def student_exam_result(request, college_slug, exam_id):
    if not request.user.is_student():
        return redirect('dashboard', college_slug=college_slug)
    student = request.user.student_profile
    exam = get_object_or_404(Exam, pk=exam_id)
    try:
        result = ExamResult.objects.get(exam=exam, student=student)
    except ExamResult.DoesNotExist:
        result = None
    return render(request, 'academics/student_exam_result.html', {
        'exam': exam, 'result': result, 'student': student,
    })


# --- NOTICES ---

@login_required
def notices(request, college_slug):
    user = request.user
    if user.is_college():
        notice_list = Notice.objects.filter(
            college=user.college_profile
        ).order_by('-created_at')
    elif user.is_teacher():
        notice_list = Notice.objects.filter(
            college=user.teacher_profile.college,
            is_active=True,
            target_audience__in=['all', 'teachers']
        ).order_by('-created_at')
    else:
        notice_list = Notice.objects.filter(
            college=user.student_profile.college,
            is_active=True,
            target_audience__in=['all', 'students']
        ).order_by('-created_at')

    for notice in notice_list:
        notice.read_by.add(user)

    paginator = Paginator(notice_list, 10)
    page_obj = paginator.get_page(request.GET.get('page'))
    return render(request, 'academics/notices.html', {'page_obj': page_obj})


@login_required
def add_notice(request, college_slug):
    if not (request.user.is_college() or request.user.is_teacher()):
        return redirect('dashboard', college_slug=college_slug)
    if request.method == 'POST':
        form = NoticeForm(request.POST)
        if form.is_valid():
            notice = form.save(commit=False)
            if request.user.is_college():
                notice.college = request.user.college_profile
            else:
                notice.college = request.user.teacher_profile.college
            notice.created_by = request.user
            notice.save()
            send_notice_email(notice)
            messages.success(request, 'Notice posted! Students/teachers will be notified by email.')
            return redirect('notices', college_slug=college_slug)
    else:
        form = NoticeForm()
    return render(request, 'academics/add_notice.html', {'form': form})


@login_required
def edit_notice(request, college_slug, pk):
    notice = get_object_or_404(Notice, pk=pk)
    user = request.user
    if user.is_student():
        messages.error(request, 'Access denied.')
        return redirect('notices', college_slug=college_slug)
    if user.is_college():
        if notice.college != user.college_profile:
            messages.error(request, 'Access denied.')
            return redirect('notices', college_slug=college_slug)
    elif user.is_teacher():
        if notice.created_by != user:
            messages.error(request, 'You can only edit notices you created.')
            return redirect('notices', college_slug=college_slug)
    if request.method == 'POST':
        form = NoticeForm(request.POST, instance=notice)
        if form.is_valid():
            form.save()
            messages.success(request, 'Notice updated!')
            return redirect('notices', college_slug=college_slug)
    else:
        form = NoticeForm(instance=notice)
    return render(request, 'academics/edit_notice.html', {'form': form, 'notice': notice})


@login_required
def delete_notice(request, college_slug, pk):
    notice = get_object_or_404(Notice, pk=pk)
    user = request.user
    if user.is_student():
        messages.error(request, 'Access denied.')
        return redirect('notices', college_slug=college_slug)
    if user.is_college():
        if notice.college != user.college_profile:
            messages.error(request, 'Access denied.')
            return redirect('notices', college_slug=college_slug)
    elif user.is_teacher():
        if notice.created_by != user:
            messages.error(request, 'You can only delete notices you created.')
            return redirect('notices', college_slug=college_slug)
    if request.method == 'POST':
        notice.delete()
        messages.success(request, 'Notice deleted.')
        return redirect('notices', college_slug=college_slug)
    return render(request, 'academics/delete_notice.html', {'notice': notice})


# --- FEES ---

@login_required
def fees(request, college_slug):
    user = request.user
    if user.is_college():
        college = user.college_profile
        fee_structures = FeeStructure.objects.filter(college=college)
        payments = FeePayment.objects.filter(
            student__college=college
        ).select_related('student__user', 'fee_structure').order_by('-payment_date')[:20]
        pending_count = FeePayment.objects.filter(student__college=college, status='pending').count()
        paid_count = FeePayment.objects.filter(student__college=college, status='paid').count()
        return render(request, 'academics/fees_college.html', {
            'fee_structures': fee_structures, 'payments': payments,
            'pending_count': pending_count, 'paid_count': paid_count
        })
    elif user.is_student():
        student = user.student_profile
        payments = FeePayment.objects.filter(
            student=student
        ).select_related('fee_structure').order_by('-payment_date')
        return render(request, 'academics/fees_student.html', {'payments': payments})
    return redirect('dashboard', college_slug=college_slug)


@login_required
def add_fee_structure(request, college_slug):
    if not request.user.is_college():
        return redirect('dashboard', college_slug=college_slug)
    college = request.user.college_profile
    if request.method == 'POST':
        form = FeeStructureForm(request.POST)
        if form.is_valid():
            fs = form.save(commit=False)
            fs.college = college
            fs.save()
            messages.success(request, 'Fee structure added!')
            return redirect('fees', college_slug=college_slug)
    else:
        form = FeeStructureForm()
    return render(request, 'academics/add_fee_structure.html', {'form': form})


@login_required
def record_payment(request, college_slug):
    if not request.user.is_college():
        return redirect('dashboard', college_slug=college_slug)
    college = request.user.college_profile
    if request.method == 'POST':
        form = FeePaymentForm(request.POST)
        form.fields['student'].queryset = StudentProfile.objects.filter(college=college)
        form.fields['fee_structure'].queryset = FeeStructure.objects.filter(college=college)
        if form.is_valid():
            form.save()
            messages.success(request, 'Payment recorded!')
            return redirect('fees', college_slug=college_slug)
    else:
        form = FeePaymentForm()
        form.fields['student'].queryset = StudentProfile.objects.filter(college=college)
        form.fields['fee_structure'].queryset = FeeStructure.objects.filter(college=college)
    return render(request, 'academics/record_payment.html', {'form': form})


@login_required
def download_fee_receipt(request, college_slug, payment_id):
    payment = get_object_or_404(FeePayment, pk=payment_id)
    if request.user.is_student():
        if payment.student != request.user.student_profile:
            messages.error(request, 'Access denied.')
            return redirect('fees', college_slug=college_slug)
    elif not request.user.is_college():
        return redirect('fees', college_slug=college_slug)

    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        rightMargin=20*mm, leftMargin=20*mm,
        topMargin=20*mm, bottomMargin=20*mm,
    )
    styles = getSampleStyleSheet()
    story = []

    PRIMARY = colors.HexColor('#4F46E5')
    LIGHT = colors.HexColor('#EEF2FF')
    MUTED = colors.HexColor('#6B7280')
    SUCCESS = colors.HexColor('#10B981')
    DANGER = colors.HexColor('#EF4444')

    college = payment.student.college
    story.append(Paragraph(
        college.college_name.upper(),
        ParagraphStyle('CollegeName', fontSize=18, fontName='Helvetica-Bold',
                       textColor=PRIMARY, alignment=TA_CENTER, spaceAfter=2)
    ))
    if college.address:
        story.append(Paragraph(
            college.address,
            ParagraphStyle('Address', fontSize=9, textColor=MUTED, alignment=TA_CENTER, spaceAfter=2)
        ))
    if college.website:
        story.append(Paragraph(
            college.website,
            ParagraphStyle('Website', fontSize=9, textColor=MUTED, alignment=TA_CENTER, spaceAfter=8)
        ))
    story.append(HRFlowable(width='100%', thickness=2, color=PRIMARY, spaceAfter=12))
    story.append(Paragraph(
        'FEE PAYMENT RECEIPT',
        ParagraphStyle('Title', fontSize=14, fontName='Helvetica-Bold',
                       textColor=PRIMARY, alignment=TA_CENTER, spaceAfter=16)
    ))
    meta_data = [[
        Paragraph(f'<b>Receipt No:</b> {payment.receipt_number or "N/A"}',
                  ParagraphStyle('meta', fontSize=10)),
        Paragraph(f'<b>Payment Date:</b> {payment.payment_date.strftime("%d %b %Y") if payment.payment_date else "—"}',
                  ParagraphStyle('metaR', fontSize=10, alignment=TA_RIGHT)),
    ]]
    meta_table = Table(meta_data, colWidths=['50%', '50%'])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT),
        ('ROWPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 14))

    student = payment.student
    story.append(Paragraph(
        'Student Information',
        ParagraphStyle('SectionHead', fontSize=11, fontName='Helvetica-Bold',
                       textColor=PRIMARY, spaceAfter=6)
    ))
    student_data = [
        ['Name', student.user.get_full_name()],
        ['Roll Number', student.roll_number or '—'],
        ['Enrollment No.', student.enrollment_number or '—'],
        ['Department', str(student.department) if student.department else '—'],
        ['Semester', f'Semester {student.semester}' if student.semester else '—'],
    ]
    student_table = Table(student_data, colWidths=[45*mm, 120*mm])
    student_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), MUTED),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, LIGHT]),
        ('ROWPADDING', (0, 0), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
    ]))
    story.append(student_table)
    story.append(Spacer(1, 14))

    story.append(Paragraph(
        'Payment Details',
        ParagraphStyle('SectionHead2', fontSize=11, fontName='Helvetica-Bold',
                       textColor=PRIMARY, spaceAfter=6)
    ))
    status_color = SUCCESS if payment.status == 'paid' else DANGER
    payment_data = [
        ['Fee Type', payment.fee_structure.name],
        ['Description', payment.fee_structure.description or '—'],
        ['Total Amount', f'Rs. {payment.fee_structure.amount}'],
        ['Amount Paid', f'Rs. {payment.amount_paid}'],
        ['Balance', f'Rs. {float(payment.fee_structure.amount) - float(payment.amount_paid)}'],
        ['Transaction ID', payment.transaction_id or '—'],
        ['Status', payment.status.upper()],
    ]
    payment_table = Table(payment_data, colWidths=[45*mm, 120*mm])
    payment_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), MUTED),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, LIGHT]),
        ('ROWPADDING', (0, 0), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#E5E7EB')),
        ('TEXTCOLOR', (1, 6), (1, 6), status_color),
        ('FONTNAME', (1, 6), (1, 6), 'Helvetica-Bold'),
        ('FONTSIZE', (1, 6), (1, 6), 11),
    ]))
    story.append(payment_table)
    story.append(Spacer(1, 24))
    story.append(HRFlowable(width='100%', thickness=1, color=colors.HexColor('#E5E7EB'), spaceAfter=10))
    story.append(Paragraph(
        'This is a computer-generated receipt and does not require a physical signature.',
        ParagraphStyle('Footer', fontSize=8, textColor=MUTED, alignment=TA_CENTER)
    ))
    story.append(Paragraph(
        f'Generated by EduCore &bull; {college.college_name}',
        ParagraphStyle('Footer2', fontSize=8, textColor=MUTED, alignment=TA_CENTER, spaceBefore=4)
    ))

    doc.build(story)
    buffer.seek(0)
    filename = f"receipt_{payment.receipt_number or payment.pk}.pdf"
    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response


@login_required
def cancel_exam(request, college_slug, exam_id):
    if not (request.user.is_college() or request.user.is_teacher()):
        return redirect('dashboard', college_slug=college_slug)
    exam = get_object_or_404(Exam, pk=exam_id)
    if request.method == 'POST':
        reason = request.POST.get('reason', '')
        exam.status = 'cancelled'
        exam.cancellation_reason = reason
        exam.save()
        # email students
        students = StudentProfile.objects.filter(
            college=exam.college,
            department=exam.course.department,
            semester=exam.course.semester
        )
        emails = [s.user.email for s in students if s.user.email]
        if emails:
            from django.core.mail import send_mail
            from django.conf import settings
            send_mail(
                f"Exam Cancelled: {exam.course.name} — {exam.get_exam_type_display()}",
                f"Dear Student,\n\nThe {exam.get_exam_type_display()} exam for {exam.course.name} "
                f"scheduled on {exam.date.strftime('%d %B %Y')} has been CANCELLED.\n"
                + (f"Reason: {reason}\n" if reason else "")
                + "\n— CampusHub",
                settings.EMAIL_HOST_USER, emails, fail_silently=True
            )
        messages.success(request, 'Exam cancelled and students notified.')
        return redirect('exams', college_slug=college_slug)
    return render(request, 'academics/cancel_exam.html', {'exam': exam, 'college_slug': college_slug})


@login_required
def postpone_exam(request, college_slug, exam_id):
    if not (request.user.is_college() or request.user.is_teacher()):
        return redirect('dashboard', college_slug=college_slug)
    exam = get_object_or_404(Exam, pk=exam_id)
    if request.method == 'POST':
        new_date = request.POST.get('new_date', '').strip()
        old_date = exam.postponed_date if exam.postponed_date else exam.date  
        exam.status = 'postponed'
        exam.postponed_date = new_date if new_date else None
        exam.save()
        students = StudentProfile.objects.filter(
            college=exam.college,
            department=exam.course.department,
            semester=exam.course.semester
        )
        emails = [s.user.email for s in students if s.user.email]
        if emails:
            from django.core.mail import send_mail
            from django.conf import settings
            date_str = new_date if new_date else "TBD"
            send_mail(
                f"Exam Postponed: {exam.course.name} — {exam.get_exam_type_display()}",
                f"Dear Student,\n\nThe {exam.get_exam_type_display()} exam for {exam.course.name} "
                f"scheduled on {old_date} has been POSTPONED.\n"
                f"New Date: {date_str}\n\n— CampusHub",
                settings.EMAIL_HOST_USER, emails, fail_silently=True
            )
        messages.success(request, 'Exam postponed and students notified.')
        return redirect('exams', college_slug=college_slug)
    return render(request, 'academics/postpone_exam.html', {'exam': exam, 'college_slug': college_slug})


@login_required
def edit_department(request, college_slug, dept_id):
    if not request.user.is_college():
        return redirect('dashboard', college_slug=college_slug)
    college = request.user.college_profile
    dept = get_object_or_404(Department, pk=dept_id, college=college)
    teachers = TeacherProfile.objects.filter(college=college)
    if request.method == 'POST':
        dept.name = request.POST.get('name', '').strip()
        dept.code = request.POST.get('code', '').strip().upper()
        dept.description = request.POST.get('description', '').strip()
        hod_id = request.POST.get('head_of_department')
        dept.head_of_department = TeacherProfile.objects.filter(pk=hod_id).first() if hod_id else None
        dept.save()
        messages.success(request, 'Department updated.')
        return redirect('departments', college_slug=college_slug)
    return render(request, 'academics/edit_department.html', {
        'dept': dept, 'teachers': teachers, 'college_slug': college_slug
    })
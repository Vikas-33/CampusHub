from django.core.mail import send_mail
from django.conf import settings


def send_notice_email(notice):
    """
    Send email to students/teachers when a new notice is posted.
    Target audience determines who gets the email.
    """
    from accounts.models import StudentProfile, TeacherProfile

    college = notice.college
    subject = f"[{college.college_name}] New Notice: {notice.title}"
    message = f"""
Hello,

A new notice has been posted on CampusHub.

Title: {notice.title}
Type: {notice.get_notice_type_display()}
Posted by: {notice.created_by.get_full_name()}

{notice.content}

---
This is an automated message from CampusHub.
Please do not reply to this email.
    """.strip()

    recipients = []

    if notice.target_audience in ['all', 'students']:
        student_emails = list(
            StudentProfile.objects.filter(
                college=college
            ).values_list('user__email', flat=True)
        )
        recipients.extend([e for e in student_emails if e])

    if notice.target_audience in ['all', 'teachers']:
        teacher_emails = list(
            TeacherProfile.objects.filter(
                college=college
            ).values_list('user__email', flat=True)
        )
        recipients.extend([e for e in teacher_emails if e])

    if recipients:
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipients,
                fail_silently=True,  # Don't crash the app if email fails
            )
        except Exception:
            pass  # Email failure should never break the app


def send_assignment_email(assignment):
    """
    Notify students when a new assignment is created for their course.
    """
    from accounts.models import StudentProfile

    course = assignment.course
    college = course.college
    subject = f"[{college.college_name}] New Assignment: {assignment.title}"
    message = f"""
Hello,

A new assignment has been posted for your course on CampusHub.

Course: {course.name} ({course.code})
Assignment: {assignment.title}
Due Date: {assignment.due_date.strftime('%d %b %Y, %I:%M %p')}
Total Marks: {assignment.total_marks}

Description:
{assignment.description}

Log in to CampusHub to submit your assignment before the deadline.

---
This is an automated message from CampusHub.
Please do not reply to this email.
    """.strip()

    # Notify students in the same department, college, semester as the course
    recipients = list(
        StudentProfile.objects.filter(
            college=college,
            department=course.department,
            semester=course.semester,
        ).values_list('user__email', flat=True)
    )
    recipients = [e for e in recipients if e]

    if recipients:
        try:
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipients,
                fail_silently=True,
            )
        except Exception:
            pass


def send_result_email(result):
    """
    Notify a student when their exam result is published.
    """
    student = result.student
    exam = result.exam
    college = student.college

    if not student.user.email:
        return

    status = "Pass ✅" if result.marks_obtained >= exam.passing_marks else "Fail ❌"
    subject = f"[{college.college_name}] Exam Result: {exam.course.name}"
    message = f"""
Hello {student.user.get_full_name()},

Your result for the following exam has been published on CampusHub.

Course: {exam.course.name}
Exam Type: {exam.get_exam_type_display()}
Date: {exam.date.strftime('%d %b %Y')}

Marks Obtained: {result.marks_obtained} / {exam.total_marks}
Grade: {result.grade or 'N/A'}
Status: {status}

Log in to CampusHub to view your full results.

---
This is an automated message from CampusHub.
Please do not reply to this email.
    """.strip()

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[student.user.email],
            fail_silently=True,
        )
    except Exception:
        pass
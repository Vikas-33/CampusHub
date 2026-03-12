from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from .forms import LoginForm, CollegeRegistrationForm, TeacherForm, StudentForm, ProfileUpdateForm
from .models import User, CollegeProfile, TeacherProfile, StudentProfile
from academics.models import Course, Notice, Attendance, FeePayment, Exam, Assignment
from accounts.models import StudentProfile
from django.core.paginator import Paginator
from academics.utils import send_teacher_credentials, send_student_credentials


# ─── Helpers ────────────────────────────────────────────────────────────────

def _get_user_slug(user):
    """Return the college slug for any user role."""
    try:
        if user.role == 'college':
            return user.college_profile.slug
        elif user.role == 'teacher':
            return user.teacher_profile.college.slug
        elif user.role == 'student':
            return user.student_profile.college.slug
    except Exception:
        return None
    return None


def _redirect_dashboard(user):
    slug = _get_user_slug(user)
    if slug:
        return redirect('dashboard', college_slug=slug)
    return redirect('login')


# ─── Auth ────────────────────────────────────────────────────────────────────

def login_view(request):
    if request.user.is_authenticated:
        return _redirect_dashboard(request.user)
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return _redirect_dashboard(user)
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


def register_college(request):
    if request.method == 'POST':
        form = CollegeRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'College registered successfully!')
            return _redirect_dashboard(user)
    else:
        form = CollegeRegistrationForm()
    return render(request, 'accounts/register_college.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


# ─── Dashboard ───────────────────────────────────────────────────────────────

@login_required
def dashboard(request, college_slug):
    user = request.user
    context = {'user': user}

    if user.is_college():
        try:
            college = user.college_profile
        except CollegeProfile.DoesNotExist:
            messages.error(request, 'College profile not found.')
            return redirect('login')
        context.update({
            'college': college,
            'total_students': StudentProfile.objects.filter(college=college).count(),
            'total_teachers': TeacherProfile.objects.filter(college=college).count(),
            'total_courses': Course.objects.filter(college=college).count(),
            'recent_notices': Notice.objects.filter(
                college=college, is_active=True
            ).order_by('-created_at')[:5],
            'upcoming_exams': Exam.objects.filter(college=college).order_by('date')[:5],
            'pending_fees': FeePayment.objects.filter(
                student__college=college, status='pending'
            ).count(),
        })
        return render(request, 'dashboards/college_dashboard.html', context)

    elif user.is_teacher():
        try:
            teacher = user.teacher_profile
        except TeacherProfile.DoesNotExist:
            messages.error(request, 'Teacher profile not found.')
            return redirect('login')
        courses = Course.objects.filter(teacher=teacher)
        context.update({
            'teacher': teacher,
            'courses': courses,
            'total_students': StudentProfile.objects.filter(college=teacher.college).count(),
            'assignments': Assignment.objects.filter(course__teacher=teacher).count(),
            'recent_notices': Notice.objects.filter(
                college=teacher.college, is_active=True,
                target_audience__in=['all', 'teachers']
            ).order_by('-created_at')[:5],
            'upcoming_exams': Exam.objects.filter(
                course__teacher=teacher
            ).order_by('date')[:5],
        })
        return render(request, 'dashboards/teacher_dashboard.html', context)

    elif user.is_student():
        try:
            student = user.student_profile
        except StudentProfile.DoesNotExist:
            messages.error(request, 'Student profile not found.')
            return redirect('login')

        courses = Course.objects.filter(
            department=student.department,
            college=student.college,
            semester=student.semester
        )
        attendance = Attendance.objects.filter(student=student)
        total = attendance.count()
        present = attendance.filter(status='present').count()
        att_percent = round((present / total * 100), 1) if total > 0 else 0

        upcoming_exams = Exam.objects.filter(
            course__in=courses
        ).order_by('date')[:5] if courses.exists() else Exam.objects.filter(
            college=student.college
        ).order_by('date')[:5]

        recent_notices = Notice.objects.filter(
            college=student.college, is_active=True,
            target_audience__in=['all', 'students']
        ).order_by('-created_at')[:5]

        context.update({
            'student': student,
            'courses': courses,
            'attendance_percent': att_percent,
            'pending_assignments': Assignment.objects.filter(course__in=courses).count(),
            'fee_dues': FeePayment.objects.filter(student=student, status='pending').count(),
            'recent_notices': recent_notices,
            'upcoming_exams': upcoming_exams,
        })
        return render(request, 'dashboards/student_dashboard.html', context)

    return redirect('login')


# ─── Profile ─────────────────────────────────────────────────────────────────

@login_required
def profile(request, college_slug):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile', college_slug=college_slug)
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form})


# ─── Teachers ────────────────────────────────────────────────────────────────

@login_required
def manage_teachers(request, college_slug):
    if not request.user.is_college():
        messages.error(request, 'Access denied.')
        return redirect('dashboard', college_slug=college_slug)
    college = request.user.college_profile
    teachers = TeacherProfile.objects.filter(college=college).select_related('user')

    search_query = request.GET.get('q', '').strip()
    dept_filter = request.GET.get('department', '')

    if search_query:
        from django.db.models import Q
        teachers = teachers.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(employee_id__icontains=search_query) |
            Q(designation__icontains=search_query) |
            Q(department__icontains=search_query)
        )
    if dept_filter:
        teachers = teachers.filter(department__icontains=dept_filter)

    from academics.models import Department
    departments = Department.objects.filter(college=college)

    paginator = Paginator(teachers, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'college/manage_teachers.html', {
        'page_obj': page_obj,
        'college': college,
        'departments': departments,
        'search_query': search_query,
        'dept_filter': dept_filter,
    })

@login_required
def add_teacher(request, college_slug):
    if not request.user.is_college():
        messages.error(request, 'Access denied.')
        return redirect('dashboard', college_slug=college_slug)
    college = request.user.college_profile

    if request.method == 'POST':
        first_name = request.POST.get('first_name', '').strip()
        last_name = request.POST.get('last_name', '').strip()
        email = request.POST.get('email', '').strip()
        department = request.POST.get('department', '').strip()
        designation = request.POST.get('designation', '').strip()
        qualification = request.POST.get('qualification', '').strip()
        specialization = request.POST.get('specialization', '').strip()
        joining_date = request.POST.get('joining_date') or None
        salary = request.POST.get('salary') or None

        if not all([first_name, last_name, email, department, designation, qualification]):
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'college/add_teacher.html')

        import time
        user = User.objects.create_user(
            username=f'tmp_{int(time.time() * 1000)}',
            email=email,
            first_name=first_name,
            last_name=last_name,
            role='teacher',
        )
        profile = TeacherProfile.objects.create(
            user=user,
            college=college,
            department=department,
            designation=designation,
            qualification=qualification,
            specialization=specialization,
            joining_date=joining_date,
            salary=salary,
        )
        # profile.save() already set username to employee_id
        user.set_password(profile.employee_id)
        user.save()
        send_teacher_credentials(profile)
        messages.success(
            request,
            f'Teacher added! Employee ID: {profile.employee_id} | Username & Password: {profile.employee_id}'
        )
        return redirect('manage_teachers', college_slug=college_slug)

    return render(request, 'college/add_teacher.html')



@login_required
def edit_teacher(request, college_slug, pk):
    if not request.user.is_college():
        return redirect('dashboard', college_slug=college_slug)
    teacher = get_object_or_404(TeacherProfile, pk=pk, college=request.user.college_profile)
    if request.method == 'POST':
        form = TeacherForm(request.POST, instance=teacher)
        if form.is_valid():
            cd = form.cleaned_data
            teacher.user.first_name = cd['first_name']
            teacher.user.last_name = cd['last_name']
            teacher.user.email = cd['email']
            teacher.user.save()
            form.save()
            messages.success(request, 'Teacher updated successfully!')
            return redirect('manage_teachers', college_slug=college_slug)
    else:
        form = TeacherForm(instance=teacher, initial={
            'first_name': teacher.user.first_name,
            'last_name': teacher.user.last_name,
            'email': teacher.user.email,
        })
    return render(request, 'college/edit_teacher.html', {'form': form, 'teacher': teacher})


@login_required
def delete_teacher(request, college_slug, pk):
    if not request.user.is_college():
        return redirect('dashboard', college_slug=college_slug)
    teacher = get_object_or_404(TeacherProfile, pk=pk, college=request.user.college_profile)
    if request.method == 'POST':
        teacher.user.delete()
        messages.success(request, 'Teacher deleted.')
        return redirect('manage_teachers', college_slug=college_slug)
    return render(request, 'college/confirm_delete.html', {'object': teacher, 'type': 'Teacher'})


# ─── Students ────────────────────────────────────────────────────────────────

@login_required
def manage_students(request, college_slug):
    if not request.user.is_college():
        return redirect('dashboard', college_slug=college_slug)
    college = request.user.college_profile
    students = StudentProfile.objects.filter(college=college).select_related('user', 'department')

    search_query = request.GET.get('q', '').strip()
    dept_filter = request.GET.get('department', '')
    sem_filter = request.GET.get('semester', '')

    if search_query:
        from django.db.models import Q
        students = students.filter(
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query) |
            Q(user__email__icontains=search_query) |
            Q(roll_number__icontains=search_query) |
            Q(enrollment_number__icontains=search_query)
        )
    if dept_filter:
        students = students.filter(department__id=dept_filter)
    if sem_filter:
        students = students.filter(semester=sem_filter)

    from academics.models import Department
    departments = Department.objects.filter(college=college)

    paginator = Paginator(students, 20)
    page_obj = paginator.get_page(request.GET.get('page'))

    return render(request, 'college/manage_students.html', {
        'page_obj': page_obj,
        'college': college,
        'departments': departments,
        'search_query': search_query,
        'dept_filter': dept_filter,
        'sem_filter': sem_filter,
    })


@login_required
def add_student(request, college_slug):
    if not request.user.is_college():
        return redirect('dashboard', college_slug=college_slug)
    college = request.user.college_profile

    if request.method == 'POST':
        form = StudentForm(request.POST, college=college)
        if form.is_valid():
            cd = form.cleaned_data
            import time
            user = User.objects.create_user(
                username=f'tmp_{int(time.time() * 1000)}',
                email=cd['email'],
                first_name=cd['first_name'],
                last_name=cd['last_name'],
                role='student',
                phone=cd.get('phone', ''),
            )
            profile = StudentProfile.objects.create(
                user=user,
                college=college,
                department=cd.get('department'),
                semester=cd['semester'],
                batch_year=cd['batch_year'],
                date_of_birth=cd.get('date_of_birth'),
                address=cd.get('address', ''),
                guardian_name=cd.get('guardian_name', ''),
                guardian_phone=cd.get('guardian_phone', ''),
            )
            # profile.save() already set username to roll_number
            user.username = profile.roll_number
            user.set_password(profile.roll_number)
            user.save()
            send_student_credentials(profile)
            messages.success(
                request,
                f'Student enrolled! Roll No: {profile.roll_number} | Username & Password: {profile.roll_number}'
            )
            return redirect('manage_students', college_slug=college_slug)
    else:
        form = StudentForm(college=college)

    return render(request, 'college/add_student.html', {'form': form})


@login_required
def edit_student(request, college_slug, pk):
    if not request.user.is_college():
        return redirect('dashboard', college_slug=college_slug)
    college = request.user.college_profile
    student = get_object_or_404(StudentProfile, pk=pk, college=college)
    if request.method == 'POST':
        form = StudentForm(request.POST, instance=student, college=college)
        if form.is_valid():
            cd = form.cleaned_data
            student.user.first_name = cd['first_name']
            student.user.last_name = cd['last_name']
            student.user.email = cd['email']
            student.user.save()
            form.save()
            messages.success(request, 'Student updated successfully!')
            return redirect('manage_students', college_slug=college_slug)
    else:
        form = StudentForm(instance=student, college=college, initial={
            'first_name': student.user.first_name,
            'last_name': student.user.last_name,
            'email': student.user.email,
        })
    return render(request, 'college/edit_student.html', {'form': form, 'student': student})


@login_required
def delete_student(request, college_slug, pk):
    if not request.user.is_college():
        return redirect('dashboard', college_slug=college_slug)
    student = get_object_or_404(StudentProfile, pk=pk, college=request.user.college_profile)
    if request.method == 'POST':
        student.user.delete()
        messages.success(request, 'Student deleted.')
        return redirect('manage_students', college_slug=college_slug)
    return render(request, 'college/confirm_delete.html', {'object': student, 'type': 'Student'})
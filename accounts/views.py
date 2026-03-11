from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from .forms import LoginForm, CollegeRegistrationForm, TeacherForm, StudentForm, ProfileUpdateForm
from .models import User, CollegeProfile, TeacherProfile, StudentProfile
from academics.models import Course, Notice, Attendance, FeePayment, Exam, Assignment
from django.core.paginator import Paginator



def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect('dashboard')
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
            return redirect('dashboard')
    else:
        form = CollegeRegistrationForm()
    return render(request, 'accounts/register_college.html', {'form': form})


def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard(request):
    print(f"DEBUG DASHBOARD CALLED: user={request.user.username} role={request.user.role}")
    user = request.user
    context = {'user': user}

    if user.is_college():
        try:
            college = user.college_profile
        except CollegeProfile.DoesNotExist:
            messages.error(request, 'College profile not found. Please contact support.')
            return redirect('login')
        context.update({
            'college': college,
            'total_students': StudentProfile.objects.filter(college=college).count(),
            'total_teachers': TeacherProfile.objects.filter(college=college).count(),
            'total_courses': Course.objects.filter(college=college).count(),
            'recent_notices': Notice.objects.filter(
                college=college,
                is_active=True
            ).order_by('-created_at')[:5],
            'upcoming_exams': Exam.objects.filter(
                college=college
            ).order_by('date')[:5],
            'pending_fees': FeePayment.objects.filter(
                student__college=college, status='pending'
            ).count(),
        })
        return render(request, 'dashboards/college_dashboard.html', context)

    elif user.is_teacher():
        try:
            teacher = user.teacher_profile
        except TeacherProfile.DoesNotExist:
            messages.error(request, 'Teacher profile not found. Please contact support.')
            return redirect('login')
        courses = Course.objects.filter(teacher=teacher)
        context.update({
            'teacher': teacher,
            'courses': courses,
            'total_students': StudentProfile.objects.filter(college=teacher.college).count(),
            'assignments': Assignment.objects.filter(course__teacher=teacher).count(),
            'recent_notices': Notice.objects.filter(
                college=teacher.college,
                is_active=True,
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
            messages.error(request, 'Student profile not found. Please contact support.')
            return redirect('login')

        # DEBUG
        test_notices = Notice.objects.filter(
            college=student.college,
            is_active=True,
            target_audience__in=['all', 'students']
        )
        print(f"DEBUG STUDENT: username={user.username} college_id={student.college_id}")
        print(f"DEBUG NOTICES COUNT: {test_notices.count()}")
        for n in test_notices:
            print(f"  - {n.title} | audience={n.target_audience} | active={n.is_active} | college_id={n.college_id}")

        courses = Course.objects.filter(
            department=student.department,
            college=student.college,
            semester=student.semester
        )
        attendance = Attendance.objects.filter(student=student)
        total = attendance.count()
        present = attendance.filter(status='present').count()
        att_percent = round((present / total * 100), 1) if total > 0 else 0

        if courses.exists():
            upcoming_exams = Exam.objects.filter(
                course__in=courses
            ).order_by('date')[:5]
        else:
            upcoming_exams = Exam.objects.filter(
                college=student.college
            ).order_by('date')[:5]

        recent_notices = Notice.objects.filter(
            college=student.college,
            is_active=True,
            target_audience__in=['all', 'students']
        ).order_by('-created_at')[:5]

        print(f"DEBUG RECENT_NOTICES QUERYSET: {recent_notices.query}")

        context.update({
            'student': student,
            'courses': courses,
            'attendance_percent': att_percent,
            'pending_assignments': Assignment.objects.filter(course__in=courses).count(),
            'fee_dues': FeePayment.objects.filter(student=student, status='pending').count(),
            'recent_notices': recent_notices,
            'upcoming_exams': upcoming_exams,
        })

        print(f"DEBUG CONTEXT NOTICES: {context['recent_notices'].count()}")

        return render(request, 'dashboards/student_dashboard.html', context)

    return redirect('login')


@login_required
def profile(request):
    if request.method == 'POST':
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
    else:
        form = ProfileUpdateForm(instance=request.user)
    return render(request, 'accounts/profile.html', {'form': form})


@login_required
def manage_teachers(request):
    if not request.user.is_college():
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
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

    paginator = Paginator(teachers, 20)  # 20 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'college/manage_teachers.html', {
        'page_obj': page_obj,
        'college': college,
        'departments': departments,
        'search_query': search_query,
        'dept_filter': dept_filter,
    })


@login_required
def add_teacher(request):
    if not request.user.is_college():
        messages.error(request, 'Access denied.')
        return redirect('dashboard')
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

        # Create user with a temp username — will be updated by TeacherProfile.save()
        from accounts.models import User
        user = User.objects.create_user(
            username=f'temp_{email}',
            email=email,
            first_name=first_name,
            last_name=last_name,
            role='teacher',
        )

        # Create profile — auto-generates employee_id and sets username + password
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

        # Set password to employee_id
        user.set_password(profile.employee_id)
        user.save()

        messages.success(
            request,
            f'Teacher added! Employee ID: {profile.employee_id} | Username & Password: {profile.employee_id}'
        )
        return redirect('manage_teachers')

    return render(request, 'college/add_teacher.html')



@login_required
def edit_teacher(request, pk):
    if not request.user.is_college():
        return redirect('dashboard')
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
            return redirect('manage_teachers')
    else:
        form = TeacherForm(instance=teacher, initial={
            'first_name': teacher.user.first_name,
            'last_name': teacher.user.last_name,
            'email': teacher.user.email,
            'username': teacher.user.username,
        })
    return render(request, 'college/edit_teacher.html', {'form': form, 'teacher': teacher})


@login_required
def delete_teacher(request, pk):
    if not request.user.is_college():
        return redirect('dashboard')
    teacher = get_object_or_404(TeacherProfile, pk=pk, college=request.user.college_profile)
    if request.method == 'POST':
        teacher.user.delete()
        messages.success(request, 'Teacher deleted.')
        return redirect('manage_teachers')
    return render(request, 'college/confirm_delete.html', {'object': teacher, 'type': 'Teacher'})


@login_required
def manage_students(request):
    if not request.user.is_college():
        return redirect('dashboard')
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

    paginator = Paginator(students, 20)  # 20 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'college/manage_students.html', {
        'page_obj': page_obj,
        'college': college,
        'departments': departments,
        'search_query': search_query,
        'dept_filter': dept_filter,
        'sem_filter': sem_filter,
    })


@login_required
def add_student(request):
    if not request.user.is_college():
        return redirect('dashboard')
    college = request.user.college_profile

    from .forms import StudentForm
    if request.method == 'POST':
        form = StudentForm(request.POST, college=college)
        if form.is_valid():
            first_name = form.cleaned_data['first_name']
            last_name = form.cleaned_data['last_name']
            email = form.cleaned_data['email']
            department = form.cleaned_data.get('department')
            semester = form.cleaned_data['semester']
            batch_year = form.cleaned_data['batch_year']
            date_of_birth = form.cleaned_data.get('date_of_birth')
            address = form.cleaned_data.get('address', '')
            guardian_name = form.cleaned_data.get('guardian_name', '')
            guardian_phone = form.cleaned_data.get('guardian_phone', '')
            phone = form.cleaned_data.get('phone', '')

            from accounts.models import User
            user = User.objects.create_user(
                username=f'temp_{email}',
                email=email,
                first_name=first_name,
                last_name=last_name,
                role='student',
                phone=phone,
            )

            # Create profile — auto-generates roll_number, enrollment_number, sets username
            profile = StudentProfile.objects.create(
                user=user,
                college=college,
                department=department,
                semester=semester,
                batch_year=batch_year,
                date_of_birth=date_of_birth,
                address=address,
                guardian_name=guardian_name,
                guardian_phone=guardian_phone,
            )

            # Set password to roll_number
            user.set_password(profile.roll_number)
            user.save()

            messages.success(
                request,
                f'Student enrolled! Roll No: {profile.roll_number} | Username & Password: {profile.roll_number}'
            )
            return redirect('manage_students')
    else:
        form = StudentForm(college=college)

    return render(request, 'college/add_student.html', {'form': form})


@login_required
def edit_student(request, pk):
    if not request.user.is_college():
        return redirect('dashboard')
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
            return redirect('manage_students')
    else:
        form = StudentForm(instance=student, college=college, initial={
            'first_name': student.user.first_name,
            'last_name': student.user.last_name,
            'email': student.user.email,
            'username': student.user.username,
        })
    return render(request, 'college/edit_student.html', {'form': form, 'student': student})


@login_required
def delete_student(request, pk):
    if not request.user.is_college():
        return redirect('dashboard')
    student = get_object_or_404(StudentProfile, pk=pk, college=request.user.college_profile)
    if request.method == 'POST':
        student.user.delete()
        messages.success(request, 'Student deleted.')
        return redirect('manage_students')
    return render(request, 'college/confirm_delete.html', {'object': student, 'type': 'Student'})
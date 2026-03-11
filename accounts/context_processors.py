from academics.models import Notice


def unread_notices(request):
    """Injects unread_notice_count into every template."""
    if request.user.is_authenticated:
        user = request.user
        if user.role == 'college':
            notices = Notice.objects.filter(college=user.college_profile, is_active=True)
        elif user.role == 'teacher':
            try:
                college = user.teacher_profile.college
                notices = Notice.objects.filter(
                    college=college,
                    is_active=True,
                    target_audience__in=['all', 'teachers']
                )
            except Exception:
                notices = Notice.objects.none()
        elif user.role == 'student':
            try:
                college = user.student_profile.college
                notices = Notice.objects.filter(
                    college=college,
                    is_active=True,
                    target_audience__in=['all', 'students']
                )
            except Exception:
                notices = Notice.objects.none()
        else:
            notices = Notice.objects.none()

        unread_count = notices.exclude(read_by=user).count()
    else:
        unread_count = 0

    # Also inject college_slug for use in all templates
    college_slug = getattr(request, 'college_slug', None)

    return {
        'unread_notice_count': unread_count,
        'college_slug': college_slug,
    }
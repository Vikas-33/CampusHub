from academics.models import Notice


def unread_notices(request):
    """
    Injects `unread_notice_count` into every template context.
    Used to show the notification badge on the Notices sidebar link.
    """
    if not request.user.is_authenticated:
        return {'unread_notice_count': 0}

    user = request.user

    try:
        if user.is_college():
            college = user.college_profile
            count = Notice.objects.filter(
                college=college,
                is_active=True
            ).exclude(
                read_by=user
            ).count()

        elif user.is_teacher():
            college = user.teacher_profile.college
            count = Notice.objects.filter(
                college=college,
                is_active=True,
                target_audience__in=['all', 'teachers']
            ).exclude(
                read_by=user
            ).count()

        elif user.is_student():
            college = user.student_profile.college
            count = Notice.objects.filter(
                college=college,
                is_active=True,
                target_audience__in=['all', 'students']
            ).exclude(
                read_by=user
            ).count()

        else:
            count = 0

    except Exception:
        count = 0

    return {'unread_notice_count': count}
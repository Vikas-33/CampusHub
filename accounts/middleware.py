from django.http import Http404
from django.urls import resolve


class CollegeSlugMiddleware:
    """
    Reads the college_slug from the URL, validates it exists,
    and attaches the college to request.college for use in views and templates.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Try to get college_slug from the URL kwargs
        try:
            resolved = resolve(request.path_info)
            college_slug = resolved.kwargs.get('college_slug')
        except Exception:
            college_slug = None

        if college_slug:
            from accounts.models import CollegeProfile
            try:
                college = CollegeProfile.objects.select_related('user').get(slug=college_slug)
                request.college = college
                request.college_slug = college_slug
            except CollegeProfile.DoesNotExist:
                raise Http404(f"College '{college_slug}' not found.")
        else:
            request.college = None
            request.college_slug = None

        response = self.get_response(request)
        return response
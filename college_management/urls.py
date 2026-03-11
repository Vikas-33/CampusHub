from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Auth URLs (no slug needed)
    path('accounts/', include('accounts.urls')),

    # Password reset (no slug needed)
    path('accounts/password-reset/', auth_views.PasswordResetView.as_view(
        template_name='registration/password_reset.html'
    ), name='password_reset'),
    path('accounts/password-reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='registration/password_reset_done.html'
    ), name='password_reset_done'),
    path('accounts/password-reset-confirm/<uidb64>/<token>/', auth_views.PasswordResetConfirmView.as_view(
        template_name='registration/password_reset_confirm.html'
    ), name='password_reset_confirm'),
    path('accounts/password-reset-complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='registration/password_reset_complete.html'
    ), name='password_reset_complete'),

    # All college-scoped URLs under /<slug>/
    path('<slug:college_slug>/', include('accounts.slug_urls')),
    path('<slug:college_slug>/', include('academics.urls')),
    path('<slug:college_slug>/', include('core.urls')),

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
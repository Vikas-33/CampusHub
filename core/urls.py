from django.urls import path
from django.views.generic import RedirectView

urlpatterns = [
    path('', RedirectView.as_view(url='/accounts/login/'), name='home'),
    path('dashboard/', RedirectView.as_view(url='/accounts/dashboard/'), name='dashboard_redirect'),
]

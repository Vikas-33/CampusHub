from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('profile/', views.profile, name='profile'),
    path('teachers/', views.manage_teachers, name='manage_teachers'),
    path('teachers/add/', views.add_teacher, name='add_teacher'),
    path('teachers/<int:pk>/edit/', views.edit_teacher, name='edit_teacher'),
    path('teachers/<int:pk>/delete/', views.delete_teacher, name='delete_teacher'),
    path('students/', views.manage_students, name='manage_students'),
    path('students/add/', views.add_student, name='add_student'),
    path('students/<int:pk>/edit/', views.edit_student, name='edit_student'),
    path('students/<int:pk>/delete/', views.delete_student, name='delete_student'),
]
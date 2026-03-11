from django import forms
from .models import Course, Department, Attendance, Assignment, AssignmentSubmission, Exam, ExamResult, Notice, FeeStructure, FeePayment

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['name', 'code', 'head_of_department', 'description']

class CourseForm(forms.ModelForm):
    class Meta:
        model = Course
        fields = ['department', 'name', 'code', 'credits', 'semester', 'teacher', 'description']

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['student', 'date', 'status', 'remarks']
        widgets = {'date': forms.DateInput(attrs={'type': 'date'})}

class AssignmentForm(forms.ModelForm):
    class Meta:
        model = Assignment
        fields = ['course', 'title', 'description', 'due_date', 'total_marks']
        widgets = {'due_date': forms.DateTimeInput(attrs={'type': 'datetime-local'})}

class AssignmentSubmissionForm(forms.ModelForm):
    class Meta:
        model = AssignmentSubmission
        fields = ['file', 'remarks']

class ExamForm(forms.ModelForm):
    class Meta:
        model = Exam
        fields = ['course', 'exam_type', 'date', 'start_time', 'end_time', 'total_marks', 'passing_marks', 'venue']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'start_time': forms.TimeInput(attrs={'type': 'time'}),
            'end_time': forms.TimeInput(attrs={'type': 'time'}),
        }

class ExamResultForm(forms.ModelForm):
    class Meta:
        model = ExamResult
        fields = ['student', 'marks_obtained', 'grade', 'remarks']


class NoticeForm(forms.ModelForm):
    class Meta:
        model = Notice
        fields = ['title', 'content', 'notice_type', 'target_audience', 'expires_at', 'is_active']
        widgets = {
            'expires_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            # Make is_active checked by default
            'is_active': forms.CheckboxInput(attrs={'checked': True}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Default is_active to True for new notices
        if not self.instance.pk:
            self.fields['is_active'].initial = True
            
            
class FeeStructureForm(forms.ModelForm):
    class Meta:
        model = FeeStructure
        fields = ['name', 'department', 'semester', 'amount', 'due_date', 'description']
        widgets = {'due_date': forms.DateInput(attrs={'type': 'date'})}

class FeePaymentForm(forms.ModelForm):
    class Meta:
        model = FeePayment
        fields = ['student', 'fee_structure', 'amount_paid', 'payment_date', 'status', 'transaction_id', 'receipt_number', 'remarks']
        widgets = {'payment_date': forms.DateInput(attrs={'type': 'date'})}

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import User, CollegeProfile, TeacherProfile, StudentProfile
from academics.models import Department


class LoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={
        'class': 'form-control', 'placeholder': 'Username'
    }))
    password = forms.CharField(widget=forms.PasswordInput(attrs={
        'class': 'form-control', 'placeholder': 'Password'
    }))


class CollegeRegistrationForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    college_name = forms.CharField(
        max_length=200,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    address = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 2})
    )
    established_year = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    website = forms.URLField(
        required=False,
        widget=forms.URLInput(attrs={'class': 'form-control'})
    )
    phone = forms.CharField(
        required=False, max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    class Meta:
        model = User
        fields = ['username', 'email']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    def clean_password2(self):
        p1 = self.cleaned_data.get('password1')
        p2 = self.cleaned_data.get('password2')
        if p1 and p2 and p1 != p2:
            raise forms.ValidationError('Passwords do not match.')
        return p2

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError('This username is already taken.')
        return username

    def clean_phone(self):
        phone = self.cleaned_data.get('phone')
        if phone:
            digits = phone.replace(' ', '').replace('-', '').replace('+', '')
            if not digits.isdigit():
                raise forms.ValidationError('Enter a valid phone number.')
        return phone

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.role = 'college'
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.phone = self.cleaned_data.get('phone', '')
        if commit:
            user.save()
            CollegeProfile.objects.create(
                user=user,
                college_name=self.cleaned_data['college_name'],
                address=self.cleaned_data['address'],
                established_year=self.cleaned_data.get('established_year'),
                website=self.cleaned_data.get('website', ''),
            )
        return user


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone', 'profile_pic']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
        }


class TeacherForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )

    class Meta:
        model = TeacherProfile
        fields = ['department', 'designation', 'qualification',
                  'joining_date', 'salary', 'specialization']
        widgets = {
            'department': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Computer Science'}),
            'designation': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Assistant Professor'}),
            'qualification': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. M.Tech, PhD'}),
            'joining_date': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Monthly Salary'}),
            'specialization': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. Machine Learning'}),
        }

    def clean_salary(self):
        salary = self.cleaned_data.get('salary')
        if salary is not None and salary < 0:
            raise forms.ValidationError('Salary cannot be negative.')
        return salary


class StudentForm(forms.ModelForm):
    first_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'})
    )
    last_name = forms.CharField(
        max_length=50,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'})
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email'})
    )
    phone = forms.CharField(
        required=False, max_length=15,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Phone'})
    )

    class Meta:
        model = StudentProfile
        fields = ['department', 'semester', 'batch_year', 'date_of_birth',
                  'address', 'guardian_name', 'guardian_phone']
        widgets = {
            'department': forms.Select(attrs={'class': 'form-control'}),
            'semester': forms.NumberInput(attrs={
                'class': 'form-control', 'min': 1, 'max': 8,
                'placeholder': 'Enter semester (1-8)'
            }),
            'batch_year': forms.NumberInput(attrs={
                'class': 'form-control', 'min': 2000, 'max': 2100,
                'placeholder': 'e.g. 2024'
            }),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'guardian_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Guardian Full Name'}),
            'guardian_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. 9876543210'}),
        }

    def __init__(self, *args, **kwargs):
        college = kwargs.pop('college', None)
        super().__init__(*args, **kwargs)
        if college:
            self.fields['department'].queryset = Department.objects.filter(college=college)
        else:
            self.fields['department'].queryset = Department.objects.none()

    def clean_semester(self):
        semester = self.cleaned_data.get('semester')
        if semester is not None and (semester < 1 or semester > 8):
            raise forms.ValidationError('Semester must be between 1 and 8.')
        return semester

    def clean_batch_year(self):
        year = self.cleaned_data.get('batch_year')
        if year is not None and (year < 2000 or year > 2100):
            raise forms.ValidationError('Enter a valid batch year (e.g. 2024).')
        return year

    def clean_guardian_phone(self):
        phone = self.cleaned_data.get('guardian_phone')
        if phone:
            if not phone.isdigit():
                raise forms.ValidationError('Phone number must contain digits only.')
            if len(phone) != 10:
                raise forms.ValidationError('Phone number must be exactly 10 digits.')
        return phone
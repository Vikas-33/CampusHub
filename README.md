# CampusHub — College Management Platform

A complete Django-based college management system with 3 user roles: **College Admin**, **Teacher**, and **Student**.

---

## Features

### College Admin
- Dashboard with stats (students, teachers, courses, pending fees)
- Manage Teachers (Add/Edit/Delete + Search)
- Manage Students (Enroll/Edit/Delete + Search + Filters + Pagination)
- Department & Course Management
- Schedule Exams & Enter Results
- Fee Structure Setup, Payment Tracking & PDF Receipt Download
- Post/Edit/Delete Notices (General, Academic, Exam, Event, Urgent)
- View Attendance Overview

### Teacher
- Dashboard with course overview and upcoming exams
- Mark Daily Attendance per Course & Export CSV
- Create & Grade Assignments
- Schedule Exams & Enter Student Results
- Post/Edit/Delete own Notices

### Student
- Personal Dashboard with attendance % and recent notices
- View Enrolled Courses & Assignments (with submission status + grades)
- Submit Assignments
- View Exam Schedule
- View Personal Exam Results & Grades
- Track Fee Payment Status & Download PDF Receipt
- View Notices (with unread badge indicator)
- Export own Attendance Report as CSV

---

## Tech Stack

- **Backend:** Python 3.12, Django 4.x
- **Database:** SQLite (development)
- **PDF Generation:** ReportLab
- **Frontend:** Custom CSS — Google Fonts (Syne + DM Sans), no UI framework

---

## Setup Guide

### Prerequisites
- Python 3.10 or higher — download from https://www.python.org/downloads/
- During Python installation on Windows, **check "Add Python to PATH"**

---

### Step 1 — Get the Project

```bash
git clone https://github.com/YOUR_USERNAME/YOUR_REPO_NAME.git
cd YOUR_REPO_NAME
```

Or click **Code → Download ZIP** on GitHub, extract it, and open a terminal in that folder.

---

### Step 2 — Create a Virtual Environment

```bash
python -m venv venv
```

Activate it:

**Windows:**
```bash
venv\Scripts\activate
```

**Mac/Linux:**
```bash
source venv/bin/activate
```

You should see `(venv)` appear in your terminal. ✅

---

### Step 3 — Install Dependencies

```bash
pip install -r requirements.txt
```

---

### Step 4 — Set Up Environment Variables

```bash
cp .env.example .env
```

Open the `.env` file in any text editor. It will look like this:

```
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
```

Replace `your-secret-key-here` with any long random string, for example:
```
SECRET_KEY=django-insecure-my-local-college-project-2024
```

It just needs to be long and random. For production, generate one at https://djecrety.ir/

> **Note:** The `.env` file is only on your machine and is never uploaded to GitHub. Every developer creates their own.

---

### Step 5 — Run Migrations

This creates the database tables:

```bash
python manage.py makemigrations
python manage.py migrate
```

---

### Step 6 — Create a Superuser (Optional)

Access the Django admin panel at `/admin/`:

```bash
python manage.py createsuperuser
```

---

### Step 7 — Run the Server

```bash
python manage.py runserver
```

Open your browser and go to: **http://127.0.0.1:8000**

---

## First Time Usage

1. Go to **http://127.0.0.1:8000/accounts/register/** to register a College account
2. Log in — you'll land on the College Admin dashboard
3. Go to **Teachers → Add Teacher** to create teacher accounts
4. Go to **Students → Enroll Student** to create student accounts
5. Teachers and Students log in at **http://127.0.0.1:8000/accounts/login/**

---

## Demo Credentials (after running demo data)

| Role | Username | Password |
|------|----------|----------|
| College Admin | `college_admin` | `admin123` |
| Teacher | `prof_sharma` | `teacher123` |
| Student | `student_rahul` | `student123` |

---

## URL Reference

| URL | Description |
|-----|-------------|
| `/accounts/login/` | Login page |
| `/accounts/register/` | Register new college |
| `/dashboard/` | Role-based dashboard |
| `/accounts/teachers/` | Manage teachers (college only) |
| `/accounts/students/` | Manage students (college only) |
| `/departments/` | Departments |
| `/courses/` | Courses |
| `/attendance/` | Attendance |
| `/assignments/` | Assignments |
| `/exams/` | Exams |
| `/notices/` | Notice board |
| `/fees/` | Fee management |
| `/admin/` | Django admin panel |

---

## Project Structure

```
COLLEGE_MANAGEMENT/
├── manage.py
├── requirements.txt
├── .env.example
├── .gitignore
├── README.md
├── college_management/     # Django project settings
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── accounts/               # Users, login, profiles, dashboards
├── academics/              # Courses, exams, notices, fees, attendance
├── administration/
├── core/
├── templates/              # All HTML templates
├── static/                 # CSS, JS, images
└── media/                  # User uploads (auto-created, not in repo)
```

---

## Common Issues

**`ModuleNotFoundError: No module named 'django'`**
→ Virtual environment is not activated. Run `source venv/bin/activate` (Mac/Linux) or `venv\Scripts\activate` (Windows)

**`python` not recognized**
→ Try `python3` instead of `python`

**Port already in use**
→ `python manage.py runserver 8080`

**Migration errors after cloning**
→ Run `python manage.py migrate` — do not delete migration files

---

## License

MIT — free to use for learning and personal projects.
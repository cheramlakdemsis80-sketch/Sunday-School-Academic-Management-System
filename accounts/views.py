from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from .forms import LoginForm
from academics.models import AcademicYear, Semester, SchoolClass, Subject, TeacherAssignment
from students.models import Student
from teachers.models import Teacher

def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard")
    form = LoginForm(request, data=request.POST or None)
    if request.method == "POST" and form.is_valid():
        login(request, form.get_user())
        return redirect("dashboard")
    return render(request, "accounts/login.html", {"form": form})

def logout_view(request):
    logout(request)
    return redirect("login")

@login_required
def dashboard(request):
    role = request.user.role
    if request.user.is_superuser or role == "ADMIN":
        context = {
            "academic_years": AcademicYear.objects.count(),
            "semesters": Semester.objects.count(),
            "classes": SchoolClass.objects.count(),
            "subjects": Subject.objects.count(),
            "students": Student.objects.count(),
            "teachers": Teacher.objects.count(),
            "assignments": TeacherAssignment.objects.count(),
        }
        return render(request, "dashboard/admin_dashboard.html", context)
    if role == "TEACHER":
        assignments = TeacherAssignment.objects.filter(teacher__user=request.user).select_related(
            "subject", "school_class", "academic_year"
        )
        return render(request, "dashboard/teacher_dashboard.html", {"assignments": assignments})
    student = getattr(request.user, "student_profile", None)
    return render(request, "dashboard/student_dashboard.html", {"student": student})

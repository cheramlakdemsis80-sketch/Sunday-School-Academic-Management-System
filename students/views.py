from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from accounts.decorators import role_required
from .forms import StudentForm
from .models import Student

@role_required("ADMIN")
def student_list(request):
    q = request.GET.get("q", "").strip()
    qs = Student.objects.select_related("school_class", "user")
    if q:
        from django.db.models import Q
        qs = qs.filter(
            Q(student_id__icontains=q) | Q(first_name__icontains=q) |
            Q(father_name__icontains=q) | Q(grandfather_name__icontains=q)
        )
    return render(request, "students/list.html", {"students": qs, "q": q})

@role_required("ADMIN")
def student_add(request):
    form = StudentForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Student created successfully.")
        return redirect("student_list")
    return render(request, "students/form.html", {"form": form, "title": "Add Student"})

@role_required("ADMIN")
def student_edit(request, pk):
    student = get_object_or_404(Student, pk=pk)
    form = StudentForm(request.POST or None, instance=student)
    if form.is_valid():
        form.save()
        messages.success(request, "Student updated successfully.")
        return redirect("student_list")
    return render(request, "students/form.html", {"form": form, "title": "Edit Student"})

@role_required("ADMIN")
def student_delete(request, pk):
    student = get_object_or_404(Student, pk=pk)
    student.user.delete()
    return redirect("student_list")

def student_profile(request):
    if not request.user.is_authenticated:
        return redirect("login")
    student = get_object_or_404(Student.objects.select_related("school_class", "school_class__academic_year"), user=request.user)
    return render(request, "students/profile.html", {"student": student})

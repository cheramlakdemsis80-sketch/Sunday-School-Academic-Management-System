from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from accounts.decorators import role_required
from academics.models import TeacherAssignment
from .forms import TeacherForm
from .models import Teacher

@role_required("ADMIN")
def teacher_list(request):
    q = request.GET.get("q", "").strip()
    qs = Teacher.objects.select_related("user")
    if q:
        from django.db.models import Q
        qs = qs.filter(
            Q(teacher_id__icontains=q) | Q(user__username__icontains=q) |
            Q(user__first_name__icontains=q) | Q(user__last_name__icontains=q)
        )
    return render(request, "teachers/list.html", {"teachers": qs, "q": q})

@role_required("ADMIN")
def teacher_add(request):
    form = TeacherForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Teacher created successfully.")
        return redirect("teacher_list")
    return render(request, "teachers/form.html", {"form": form, "title": "Add Teacher"})

@role_required("ADMIN")
def teacher_edit(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    form = TeacherForm(request.POST or None, instance=teacher)
    if form.is_valid():
        form.save()
        messages.success(request, "Teacher updated successfully.")
        return redirect("teacher_list")
    return render(request, "teachers/form.html", {"form": form, "title": "Edit Teacher"})

@role_required("ADMIN")
def teacher_delete(request, pk):
    teacher = get_object_or_404(Teacher, pk=pk)
    teacher.user.delete()
    return redirect("teacher_list")

def teacher_profile(request):
    if not request.user.is_authenticated:
        return redirect("login")
    teacher = get_object_or_404(Teacher, user=request.user)
    assignments = TeacherAssignment.objects.filter(teacher=teacher).select_related("subject", "school_class", "academic_year")
    return render(request, "teachers/profile.html", {"teacher": teacher, "assignments": assignments})

def teacher_assignments(request):
    if not request.user.is_authenticated:
        return redirect("login")
    teacher = get_object_or_404(Teacher, user=request.user)
    assignments = TeacherAssignment.objects.filter(teacher=teacher).select_related("subject", "school_class", "academic_year")
    return render(request, "teachers/assignments.html", {"assignments": assignments})

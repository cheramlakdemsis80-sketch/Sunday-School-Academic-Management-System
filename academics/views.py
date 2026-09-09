from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from accounts.decorators import role_required
from .forms import AcademicYearForm, SemesterForm, SchoolClassForm, SubjectForm, TeacherAssignmentForm
from .models import AcademicYear, Semester, SchoolClass, Subject, TeacherAssignment

@role_required("ADMIN")
def admin_home(request):
    context = {
        "academic_years": AcademicYear.objects.count(),
        "semesters": Semester.objects.count(),
        "classes": SchoolClass.objects.count(),
        "subjects": Subject.objects.count(),
        "students": __import__("students.models", fromlist=["Student"]).Student.objects.count(),
        "teachers": __import__("teachers.models", fromlist=["Teacher"]).Teacher.objects.count(),
        "assignments": TeacherAssignment.objects.count(),
    }
    context["links"] = [
        ("../admin-panel/years/", "Academic Years", context["academic_years"]),
        ("../admin-panel/semesters/", "Semesters", context["semesters"]),
        ("../admin-panel/classes/", "Classes", context["classes"]),
        ("../admin-panel/subjects/", "Subjects", context["subjects"]),
        ("../../students/admin-panel/", "Students", context["students"]),
        ("../../teachers/admin-panel/", "Teachers", context["teachers"]),
        ("../admin-panel/assignments/", "Assignments", context["assignments"]),
    ]
    return render(request, "academics/admin_home.html", context)

def crud_list(request, model, template, title, create_url, search_fields=None):
    q = request.GET.get("q", "").strip()
    qs = model.objects.all()
    if q and search_fields:
        from django.db.models import Q
        query = Q()
        for field in search_fields:
            query |= Q(**{f"{field}__icontains": q})
        qs = qs.filter(query)
    return render(request, template, {"objects": qs, "title": title, "create_url": create_url, "q": q})

@role_required("ADMIN")
def years(request):
    return crud_list(request, AcademicYear, "academics/list.html", "Academic Years", "year_add", ["name"])

@role_required("ADMIN")
def year_add(request):
    form = AcademicYearForm(request.POST or None)
    if form.is_valid():
        form.save()
        messages.success(request, "Academic year saved.")
        return redirect("years")
    return render(request, "academics/form.html", {"form": form, "title": "Add Academic Year", "back_url": "years"})

@role_required("ADMIN")
def year_edit(request, pk):
    obj = get_object_or_404(AcademicYear, pk=pk)
    form = AcademicYearForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        messages.success(request, "Academic year updated.")
        return redirect("years")
    return render(request, "academics/form.html", {"form": form, "title": "Edit Academic Year", "back_url": "years"})

@role_required("ADMIN")
def year_delete(request, pk):
    get_object_or_404(AcademicYear, pk=pk).delete()
    return redirect("years")

@role_required("ADMIN")
def semesters(request):
    return crud_list(request, Semester, "academics/list.html", "Semesters", "semester_add", None)

@role_required("ADMIN")
def semester_add(request):
    form = SemesterForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect("semesters")
    return render(request, "academics/form.html", {"form": form, "title": "Add Semester", "back_url": "semesters"})

@role_required("ADMIN")
def semester_edit(request, pk):
    obj = get_object_or_404(Semester, pk=pk)
    form = SemesterForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        return redirect("semesters")
    return render(request, "academics/form.html", {"form": form, "title": "Edit Semester", "back_url": "semesters"})

@role_required("ADMIN")
def semester_delete(request, pk):
    get_object_or_404(Semester, pk=pk).delete()
    return redirect("semesters")

@role_required("ADMIN")
def classes(request):
    return crud_list(request, SchoolClass, "academics/list.html", "Classes / Sections", "class_add", ["grade", "section"])

@role_required("ADMIN")
def class_add(request):
    form = SchoolClassForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect("classes")
    return render(request, "academics/form.html", {"form": form, "title": "Add Class / Section", "back_url": "classes"})

@role_required("ADMIN")
def class_edit(request, pk):
    obj = get_object_or_404(SchoolClass, pk=pk)
    form = SchoolClassForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        return redirect("classes")
    return render(request, "academics/form.html", {"form": form, "title": "Edit Class / Section", "back_url": "classes"})

@role_required("ADMIN")
def class_delete(request, pk):
    get_object_or_404(SchoolClass, pk=pk).delete()
    return redirect("classes")

@role_required("ADMIN")
def subjects(request):
    return crud_list(request, Subject, "academics/list.html", "Subjects", "subject_add", ["name", "code"])

@role_required("ADMIN")
def subject_add(request):
    form = SubjectForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect("subjects")
    return render(request, "academics/form.html", {"form": form, "title": "Add Subject", "back_url": "subjects"})

@role_required("ADMIN")
def subject_edit(request, pk):
    obj = get_object_or_404(Subject, pk=pk)
    form = SubjectForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        return redirect("subjects")
    return render(request, "academics/form.html", {"form": form, "title": "Edit Subject", "back_url": "subjects"})

@role_required("ADMIN")
def subject_delete(request, pk):
    get_object_or_404(Subject, pk=pk).delete()
    return redirect("subjects")

@role_required("ADMIN")
def assignments(request):
    qs = TeacherAssignment.objects.select_related("teacher", "subject", "school_class", "academic_year")
    return render(request, "academics/assignments.html", {"objects": qs})

@role_required("ADMIN")
def assignment_add(request):
    form = TeacherAssignmentForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect("assignments")
    return render(request, "academics/form.html", {"form": form, "title": "Add Teacher Assignment", "back_url": "assignments"})

@role_required("ADMIN")
def assignment_edit(request, pk):
    obj = get_object_or_404(TeacherAssignment, pk=pk)
    form = TeacherAssignmentForm(request.POST or None, instance=obj)
    if form.is_valid():
        form.save()
        return redirect("assignments")
    return render(request, "academics/form.html", {"form": form, "title": "Edit Teacher Assignment", "back_url": "assignments"})

@role_required("ADMIN")
def assignment_delete(request, pk):
    get_object_or_404(TeacherAssignment, pk=pk).delete()
    return redirect("assignments")

from decimal import Decimal, InvalidOperation
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from accounts.decorators import role_required
from academics.models import Semester, TeacherAssignment
from students.models import Student
from teachers.models import Teacher
from .models import Result

COMPONENTS = [("midterm_mark","Midterm","midterm_max"),("assignment_mark","Assignment","assignment_max"),("summary_mark","Summary","summary_max"),("exam_mark","Exam","exam_max"),("notebook_mark","Notebook","notebook_max")]

@role_required("TEACHER")
def teacher_result_home(request):
    teacher=get_object_or_404(Teacher,user=request.user)
    assignments=TeacherAssignment.objects.filter(teacher=teacher,subject__is_active=True).select_related("subject","school_class","academic_year").prefetch_related("academic_year__semesters")
    active_semester=Semester.objects.filter(is_active=True,academic_year__is_active=True).first()
    return render(request,"results/teacher_home.html",{"assignments":assignments,"active_semester":active_semester})

@role_required("TEACHER")
def enter_results(request,assignment_id,semester_id):
    teacher=get_object_or_404(Teacher,user=request.user,status=Teacher.Status.ACTIVE)
    assignment=get_object_or_404(TeacherAssignment.objects.select_related("subject","school_class","academic_year"),pk=assignment_id,teacher=teacher,subject__is_active=True)
    semester=get_object_or_404(Semester,pk=semester_id,academic_year=assignment.academic_year)
    if not semester.is_active or not semester.academic_year.is_active:
        messages.error(request,"You can enter results only for the currently active semester and academic year.")
        return redirect("teacher_result_home")
    students=Student.objects.filter(school_class=assignment.school_class,status=Student.Status.ACTIVE).select_related("user")
    existing={r.student_id:r for r in Result.objects.filter(teacher_assignment=assignment,semester=semester)}
    if request.method=="POST":
        action=request.POST.get("action","save")
        errors=[]
        with transaction.atomic():
            for student in students:
                result=existing.get(student.pk) or Result(student=student,subject=assignment.subject,semester=semester,teacher_assignment=assignment)
                if result.status==Result.Status.SUBMITTED and action=="save": continue
                values={}
                for field,label,maximum_field in COMPONENTS:
                    raw=request.POST.get(f"{field}_{student.pk}","").strip()
                    if raw=="":
                        raw="0"
                    try: value=Decimal(raw)
                    except InvalidOperation: errors.append(f"{student.full_name}: invalid {label} mark"); continue
                    maximum=getattr(assignment.subject,maximum_field)
                    if value<0 or value>maximum: errors.append(f"{student.full_name}: {label} must be between 0 and {maximum}"); continue
                    values[field]=value
                result.remarks=request.POST.get(f"remarks_{student.pk}","").strip()
                if len(values)==len(COMPONENTS):
                    for field in values: setattr(result,field,values[field])
                    result.status=Result.Status.DRAFT
                    result.rejection_reason=""
                    result.full_clean(); result.save(); existing[student.pk]=result
            if not errors and action=="submit":
                now=timezone.now()
                Result.objects.filter(teacher_assignment=assignment,semester=semester).update(status=Result.Status.SUBMITTED,submitted_at=now,rejection_reason="",updated_at=now)
            if errors: transaction.set_rollback(True)
        if errors:
            for e in errors: messages.error(request,e)
        else:
            messages.success(request,"Results submitted successfully." if action=="submit" else "Draft results saved successfully.")
            if action=="submit": return redirect("teacher_result_home")
        existing={r.student_id:r for r in Result.objects.filter(teacher_assignment=assignment,semester=semester)}
    return render(request,"results/enter.html",{"assignment":assignment,"semester":semester,"students":students,"results":existing,"components":COMPONENTS})

@role_required("ADMIN")
def admin_results(request):
    status=request.GET.get("status","SUBMITTED")
    qs=Result.objects.select_related("student","subject","semester","teacher_assignment__teacher","teacher_assignment__school_class","approved_by")
    if status and status!="ALL": qs=qs.filter(status=status)
    return render(request,"results/admin_results.html",{"results":qs,"status":status})

@role_required("ADMIN")
def approve_result(request,pk):
    if request.method!="POST": return redirect("admin_results")
    result=get_object_or_404(Result,pk=pk)
    if result.status!=Result.Status.SUBMITTED:
        messages.error(request,"Only submitted results can be approved.")
    else:
        result.status=Result.Status.APPROVED; result.approved_at=timezone.now(); result.approved_by=request.user; result.rejection_reason=""; result.save()
        # Phase 5: when all subjects assigned to the student's class have approved results,
        # automatically create the semester certificate record.
        from certificates.models import Certificate
        required = set(TeacherAssignment.objects.filter(
            school_class=result.student.school_class, academic_year=result.semester.academic_year, subject__is_active=True
        ).values_list("subject_id", flat=True).distinct())
        approved = set(Result.objects.filter(
            student=result.student, semester=result.semester, status=Result.Status.APPROVED, subject__is_active=True
        ).values_list("subject_id", flat=True).distinct())
        if required and required.issubset(approved):
            cert, created = Certificate.objects.get_or_create(
                student=result.student, semester=result.semester,
                defaults={"certificate_number": f"SS-{result.semester.academic_year.name.replace(' ', '')}-{result.semester.get_name_display().replace(' ', '')}-{result.student.student_id}"}
            )
        messages.success(request,"Result approved. Certificate is generated automatically when all required subject results are approved.")
    return redirect(request.POST.get("next") or "admin_results")

@role_required("ADMIN")
def reject_result(request,pk):
    if request.method!="POST": return redirect("admin_results")
    result=get_object_or_404(Result,pk=pk)
    if result.status!=Result.Status.SUBMITTED:
        messages.error(request,"Only submitted results can be rejected.")
    else:
        result.status=Result.Status.REJECTED; result.rejection_reason=request.POST.get("rejection_reason","").strip()[:255]; result.approved_by=None; result.approved_at=None; result.save(); messages.warning(request,"Result rejected and returned to the teacher.")
    return redirect(request.POST.get("next") or "admin_results")

@login_required
def student_results(request):
    if request.user.role!="STUDENT": raise PermissionDenied
    student=get_object_or_404(Student,user=request.user)
    results=list(Result.objects.filter(student=student,status=Result.Status.APPROVED).select_related("subject","semester","semester__academic_year"))
    semesters={r.semester_id:r.semester for r in results}
    grouped={}
    for r in results: grouped.setdefault(r.semester_id,[]).append(r)
    summaries=[]
    for sid,items in grouped.items():
        total=sum((r.mark for r in items),Decimal("0")); maximum=sum((r.subject.max_mark for r in items),Decimal("0")); average=(total/len(items)) if items else Decimal("0"); passed=sum(1 for r in items if r.is_passed)
        summaries.append({"semester":semesters[sid],"items":items,"total":total,"maximum":maximum,"average":average,"passed":passed,"count":len(items)})
    # Rank among active students in the same class for each semester, using approved totals.
    for summary in summaries:
        sid=summary["semester"].id
        peers=Student.objects.filter(school_class=student.school_class,status=Student.Status.ACTIVE)
        totals=[]
        for peer in peers:
            rs=Result.objects.filter(student=peer,semester_id=sid,status=Result.Status.APPROVED)
            if rs.exists(): totals.append(sum((r.mark for r in rs),Decimal("0")))
        summary["rank"]=1+sum(1 for t in totals if t>summary["total"])
        summary["class_count"]=len(totals)
    summaries.sort(key=lambda x:x["semester"].name)
    return render(request,"results/student_results.html",{"student":student,"summaries":summaries})

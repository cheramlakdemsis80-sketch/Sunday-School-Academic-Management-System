from django.contrib import admin
from .models import AcademicYear, Semester, SchoolClass, Subject, TeacherAssignment
@admin.register(AcademicYear)
class AcademicYearAdmin(admin.ModelAdmin):
    list_display=("name","start_date","end_date","is_active"); list_filter=("is_active",)
@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display=("academic_year","name","start_date","end_date","is_active"); list_filter=("name","is_active","academic_year")
@admin.register(SchoolClass)
class SchoolClassAdmin(admin.ModelAdmin): list_display=("display_name","academic_year","grade","section")
@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display=("name","code","midterm_max","assignment_max","summary_max","exam_max","notebook_max","max_mark","pass_mark","is_active")
    list_filter=("is_active",); search_fields=("name","code")
@admin.register(TeacherAssignment)
class TeacherAssignmentAdmin(admin.ModelAdmin):
    list_display=("teacher","subject","school_class","academic_year"); list_filter=("academic_year","subject","school_class")

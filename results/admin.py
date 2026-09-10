from django.contrib import admin
from .models import Result
@admin.register(Result)
class ResultAdmin(admin.ModelAdmin):
    list_display=("student","subject","semester","midterm_mark","assignment_mark","summary_mark","exam_mark","notebook_mark","mark","status","submitted_at")
    list_filter=("status","semester","subject")
    search_fields=("student__student_id","student__first_name","student__father_name","subject__name")
    readonly_fields=("mark","submitted_at","approved_at","created_at","updated_at")

from django.contrib import admin
from .models import Student

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ("student_id", "full_name", "school_class", "gender", "phone", "status")
    search_fields = ("student_id", "first_name", "father_name", "grandfather_name")
    list_filter = ("status", "gender", "school_class")

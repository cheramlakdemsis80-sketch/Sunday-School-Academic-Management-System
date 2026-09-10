from django.contrib import admin
from .models import Certificate


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ("certificate_number", "student", "semester", "issued_at")
    search_fields = ("certificate_number", "student__student_id", "student__first_name", "student__father_name")
    list_filter = ("semester__academic_year", "semester__name")
    readonly_fields = ("verification_token", "issued_at")
    fields = (
        "student", "semester", "certificate_number", "grading_rule", "admin_comment",
        "verification_token", "issued_at",
    )

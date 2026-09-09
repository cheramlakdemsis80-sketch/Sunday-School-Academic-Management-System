from django.contrib import admin
from .models import Teacher

@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ("teacher_id", "name", "phone", "status")
    search_fields = ("teacher_id", "user__username", "user__first_name", "user__last_name")
    list_filter = ("status",)

    @admin.display(description="Name")
    def name(self, obj):
        return obj.user.get_full_name() or obj.user.username

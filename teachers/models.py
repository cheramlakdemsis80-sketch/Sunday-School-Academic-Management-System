from django.conf import settings
from django.db import models

class Teacher(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="teacher_profile")
    teacher_id = models.CharField(max_length=50, unique=True)
    phone = models.CharField(max_length=30, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)

    class Meta:
        ordering = ["teacher_id"]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.teacher_id})"

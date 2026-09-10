from django.conf import settings
from django.db import models

class Student(models.Model):
    class Gender(models.TextChoices):
        MALE = "M", "Male"
        FEMALE = "F", "Female"

    class Status(models.TextChoices):
        ACTIVE = "ACTIVE", "Active"
        INACTIVE = "INACTIVE", "Inactive"

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="student_profile")
    student_id = models.CharField(max_length=50, unique=True)
    first_name = models.CharField(max_length=100)
    father_name = models.CharField(max_length=100)
    grandfather_name = models.CharField(max_length=100, blank=True)
    gender = models.CharField(max_length=1, choices=Gender.choices, blank=True)
    birth_date = models.DateField(blank=True, null=True)
    school_class = models.ForeignKey("academics.SchoolClass", on_delete=models.PROTECT, related_name="students")
    phone = models.CharField(max_length=30, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["first_name", "father_name"]

    def __str__(self):
        return f"{self.first_name} {self.father_name} ({self.student_id})"

    @property
    def full_name(self):
        return " ".join(x for x in [self.first_name, self.father_name, self.grandfather_name] if x)

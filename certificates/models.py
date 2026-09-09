import uuid
from django.db import models

DEFAULT_GRADING_RULE = """100 – 90  →  በጣም ጥሩ
89 – 80   →  ጥሩ
79 – 60   → መካከለኛ
59 – 50   → ደካማ / አልፏል
ከ 50 በታች → አላለፈም"""


class Certificate(models.Model):
    student = models.ForeignKey("students.Student", on_delete=models.CASCADE, related_name="certificates")
    semester = models.ForeignKey("academics.Semester", on_delete=models.PROTECT, related_name="certificates")
    certificate_number = models.CharField(max_length=60, unique=True)
    verification_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    issued_at = models.DateTimeField(auto_now_add=True)
    grading_rule = models.TextField(blank=True, default=DEFAULT_GRADING_RULE)
    admin_comment = models.TextField(blank=True, default="")

    class Meta:
        ordering = ["-issued_at"]
        constraints = [
            models.UniqueConstraint(fields=["student", "semester"], name="unique_certificate_student_semester")
        ]

    def __str__(self):
        return f"{self.certificate_number} - {self.student.full_name}"

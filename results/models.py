from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from decimal import Decimal

class Result(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        SUBMITTED = "SUBMITTED", "Submitted"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
    student = models.ForeignKey("students.Student", on_delete=models.CASCADE, related_name="results")
    subject = models.ForeignKey("academics.Subject", on_delete=models.PROTECT, related_name="results")
    semester = models.ForeignKey("academics.Semester", on_delete=models.PROTECT, related_name="results")
    teacher_assignment = models.ForeignKey("academics.TeacherAssignment", on_delete=models.PROTECT, related_name="results")
    midterm_mark = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    assignment_mark = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    summary_mark = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    exam_mark = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    notebook_mark = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    mark = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    remarks = models.CharField(max_length=255, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    submitted_at = models.DateTimeField(blank=True, null=True)
    approved_at = models.DateTimeField(blank=True, null=True)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True, related_name="approved_results")
    rejection_reason = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["student", "subject", "semester"], name="unique_student_subject_semester_result")]
        ordering = ["student__first_name", "student__father_name"]
    def calculate_total(self):
        return sum([self.midterm_mark or Decimal("0"), self.assignment_mark or Decimal("0"), self.summary_mark or Decimal("0"), self.exam_mark or Decimal("0"), self.notebook_mark or Decimal("0")])
    def clean(self):
        if self.semester.academic_year_id != self.teacher_assignment.academic_year_id:
            raise ValidationError("Semester and teacher assignment must belong to the same academic year.")
        if self.subject_id != self.teacher_assignment.subject_id:
            raise ValidationError("Result subject must match the teacher assignment subject.")
        if self.student.school_class_id != self.teacher_assignment.school_class_id:
            raise ValidationError("Student class must match the teacher assignment class.")
        limits = [("Midterm", self.midterm_mark, self.subject.midterm_max), ("Assignment", self.assignment_mark, self.subject.assignment_max), ("Summary", self.summary_mark, self.subject.summary_max), ("Exam", self.exam_mark, self.subject.exam_max), ("Notebook", self.notebook_mark, self.subject.notebook_max)]
        for label, value, maximum in limits:
            if value is not None and (value < 0 or value > maximum):
                raise ValidationError(f"{label} mark must be between 0 and {maximum}.")
        self.mark = self.calculate_total()
    def save(self, *args, **kwargs):
        self.mark = self.calculate_total()
        super().save(*args, **kwargs)
    @property
    def is_passed(self): return self.mark >= self.subject.pass_mark
    def __str__(self): return f"{self.student} - {self.subject} - {self.semester} - {self.mark}"

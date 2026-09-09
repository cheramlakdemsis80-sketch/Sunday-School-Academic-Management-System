from django.db import models

class AcademicYear(models.Model):
    name = models.CharField(max_length=30, unique=True)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=False)

    class Meta:
        ordering = ["-id"]

    def save(self, *args, **kwargs):
        if self.is_active:
            AcademicYear.objects.exclude(pk=self.pk).update(is_active=False)
        return super().save(*args, **kwargs)

    def __str__(self): return self.name

class Semester(models.Model):
    class Names(models.TextChoices):
        FIRST = "SEMESTER_1", "Semester 1"
        SECOND = "SEMESTER_2", "Semester 2"
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name="semesters")
    name = models.CharField(max_length=20, choices=Names.choices)
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)
    is_active = models.BooleanField(default=False)
    class Meta:
        constraints = [models.UniqueConstraint(fields=["academic_year", "name"], name="unique_semester_per_year")]
        ordering = ["academic_year_id", "name"]
    def save(self, *args, **kwargs):
        if self.is_active:
            Semester.objects.filter(academic_year=self.academic_year).exclude(pk=self.pk).update(is_active=False)
        return super().save(*args, **kwargs)
    def __str__(self): return f"{self.academic_year} - {self.get_name_display()}"

class SchoolClass(models.Model):
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name="classes")
    grade = models.CharField(max_length=30)
    section = models.CharField(max_length=20, default="A")
    class Meta:
        constraints = [models.UniqueConstraint(fields=["academic_year", "grade", "section"], name="unique_class_per_year")]
        ordering = ["grade", "section"]
    @property
    def display_name(self): return f"Grade {self.grade} - Section {self.section}"
    def __str__(self): return f"{self.display_name} ({self.academic_year})"

class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=30, unique=True)
    # Total is automatically maintained as the sum of the five assessment components.
    max_mark = models.DecimalField(max_digits=6, decimal_places=2, default=100)
    midterm_max = models.DecimalField(max_digits=6, decimal_places=2, default=20)
    assignment_max = models.DecimalField(max_digits=6, decimal_places=2, default=20)
    summary_max = models.DecimalField(max_digits=6, decimal_places=2, default=20)
    exam_max = models.DecimalField(max_digits=6, decimal_places=2, default=20)
    notebook_max = models.DecimalField(max_digits=6, decimal_places=2, default=20)
    pass_mark = models.DecimalField(max_digits=6, decimal_places=2, default=50)
    is_active = models.BooleanField(default=True)
    class Meta: ordering = ["name"]
    @property
    def component_max_total(self):
        return sum([self.midterm_max, self.assignment_max, self.summary_max, self.exam_max, self.notebook_max])
    def save(self, *args, **kwargs):
        self.max_mark = self.component_max_total
        super().save(*args, **kwargs)
    def __str__(self): return f"{self.name} ({self.code})"

class TeacherAssignment(models.Model):
    teacher = models.ForeignKey("teachers.Teacher", on_delete=models.CASCADE, related_name="assignments")
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name="assignments")
    school_class = models.ForeignKey(SchoolClass, on_delete=models.CASCADE, related_name="assignments")
    academic_year = models.ForeignKey(AcademicYear, on_delete=models.CASCADE, related_name="assignments")
    class Meta:
        constraints = [models.UniqueConstraint(fields=["teacher", "subject", "school_class", "academic_year"], name="unique_teacher_assignment")]
    def __str__(self): return f"{self.teacher} - {self.subject} - {self.school_class}"

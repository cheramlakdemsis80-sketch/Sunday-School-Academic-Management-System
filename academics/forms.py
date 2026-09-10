from django import forms
from .models import AcademicYear, Semester, SchoolClass, Subject, TeacherAssignment
class DateFormMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            if isinstance(field.widget, forms.DateInput):
                field.widget = forms.DateInput(attrs={"type":"date","class":"form-control"}, format="%Y-%m-%d")
                field.input_formats=["%Y-%m-%d"]
class AcademicYearForm(DateFormMixin, forms.ModelForm):
    class Meta: model=AcademicYear; fields=["name","start_date","end_date","is_active"]
class SemesterForm(DateFormMixin, forms.ModelForm):
    class Meta: model=Semester; fields=["academic_year","name","start_date","end_date","is_active"]
class SchoolClassForm(forms.ModelForm):
    class Meta: model=SchoolClass; fields=["academic_year","grade","section"]
class SubjectForm(forms.ModelForm):
    class Meta:
        model=Subject
        fields=["name","code","midterm_max","assignment_max","summary_max","exam_max","notebook_max","pass_mark","is_active"]
        labels={"midterm_max":"Midterm maximum","assignment_max":"Assignment maximum","summary_max":"Summary maximum","exam_max":"Exam maximum","notebook_max":"Notebook maximum","pass_mark":"Pass mark"}
class TeacherAssignmentForm(forms.ModelForm):
    class Meta: model=TeacherAssignment; fields=["teacher","subject","school_class","academic_year"]

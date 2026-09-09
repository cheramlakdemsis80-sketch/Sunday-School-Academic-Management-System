from django import forms
from django.contrib.auth import get_user_model
from django.db import transaction
from .models import Student

User = get_user_model()

class StudentForm(forms.ModelForm):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput, required=False, help_text="Required when creating a student.")
    class Meta:
        model = Student
        fields = [
            "username", "password", "student_id", "first_name", "father_name",
            "grandfather_name", "gender", "birth_date", "school_class", "phone", "status"
        ]
        widgets = {"birth_date": forms.DateInput(attrs={"type": "date"}, format="%Y-%m-%d")}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs["class"] = "form-control"
        self.fields["gender"].widget.attrs["class"] = "form-select"
        self.fields["school_class"].widget.attrs["class"] = "form-select"
        self.fields["status"].widget.attrs["class"] = "form-select"
        if self.instance and self.instance.pk:
            self.fields["username"].initial = self.instance.user.username

    @transaction.atomic
    def save(self, commit=True):
        student = super().save(commit=False)
        if student.pk:
            user = student.user
            user.username = self.cleaned_data["username"]
            if self.cleaned_data.get("password"):
                user.set_password(self.cleaned_data["password"])
            user.first_name = self.cleaned_data["first_name"]
            user.last_name = self.cleaned_data["father_name"]
            user.role = User.Roles.STUDENT
            user.save()
        else:
            user = User.objects.create_user(
                username=self.cleaned_data["username"],
                password=self.cleaned_data["password"] or "ChangeMe123!",
                first_name=self.cleaned_data["first_name"],
                last_name=self.cleaned_data["father_name"],
                role=User.Roles.STUDENT,
            )
            student.user = user
        if commit:
            student.save()
        return student

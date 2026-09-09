from django import forms
from django.contrib.auth import get_user_model
from django.db import transaction
from .models import Teacher

User = get_user_model()

class TeacherForm(forms.ModelForm):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput, required=False)
    first_name = forms.CharField(max_length=150)
    last_name = forms.CharField(max_length=150)

    class Meta:
        model = Teacher
        fields = ["username", "password", "first_name", "last_name", "teacher_id", "phone", "status"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for f in self.fields.values():
            f.widget.attrs["class"] = "form-control"
        self.fields["status"].widget.attrs["class"] = "form-select"
        if self.instance and self.instance.pk:
            self.fields["username"].initial = self.instance.user.username
            self.fields["first_name"].initial = self.instance.user.first_name
            self.fields["last_name"].initial = self.instance.user.last_name

    @transaction.atomic
    def save(self, commit=True):
        teacher = super().save(commit=False)
        if teacher.pk:
            user = teacher.user
            user.username = self.cleaned_data["username"]
            user.first_name = self.cleaned_data["first_name"]
            user.last_name = self.cleaned_data["last_name"]
            user.role = User.Roles.TEACHER
            if self.cleaned_data.get("password"):
                user.set_password(self.cleaned_data["password"])
            user.save()
        else:
            user = User.objects.create_user(
                username=self.cleaned_data["username"],
                password=self.cleaned_data["password"] or "ChangeMe123!",
                first_name=self.cleaned_data["first_name"],
                last_name=self.cleaned_data["last_name"],
                role=User.Roles.TEACHER,
            )
            teacher.user = user
        if commit:
            teacher.save()
        return teacher

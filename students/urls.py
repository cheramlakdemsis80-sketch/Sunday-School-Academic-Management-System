from django.urls import path
from . import views

urlpatterns = [
    path("profile/", views.student_profile, name="student_profile"),
    path("admin-panel/", views.student_list, name="student_list"),
    path("admin-panel/add/", views.student_add, name="student_add"),
    path("admin-panel/<int:pk>/edit/", views.student_edit, name="student_edit"),
    path("admin-panel/<int:pk>/delete/", views.student_delete, name="student_delete"),
]

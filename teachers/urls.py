from django.urls import path
from . import views

urlpatterns = [
    path("profile/", views.teacher_profile, name="teacher_profile"),
    path("assignments/", views.teacher_assignments, name="teacher_assignments"),
    path("admin-panel/", views.teacher_list, name="teacher_list"),
    path("admin-panel/add/", views.teacher_add, name="teacher_add"),
    path("admin-panel/<int:pk>/edit/", views.teacher_edit, name="teacher_edit"),
    path("admin-panel/<int:pk>/delete/", views.teacher_delete, name="teacher_delete"),
]

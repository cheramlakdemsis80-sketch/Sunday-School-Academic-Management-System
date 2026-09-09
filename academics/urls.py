from django.urls import path
from . import views

urlpatterns = [
    path("admin-panel/", views.admin_home, name="admin_home"),
    path("admin-panel/years/", views.years, name="years"),
    path("admin-panel/years/add/", views.year_add, name="year_add"),
    path("admin-panel/years/<int:pk>/edit/", views.year_edit, name="year_edit"),
    path("admin-panel/years/<int:pk>/delete/", views.year_delete, name="year_delete"),
    path("admin-panel/semesters/", views.semesters, name="semesters"),
    path("admin-panel/semesters/add/", views.semester_add, name="semester_add"),
    path("admin-panel/semesters/<int:pk>/edit/", views.semester_edit, name="semester_edit"),
    path("admin-panel/semesters/<int:pk>/delete/", views.semester_delete, name="semester_delete"),
    path("admin-panel/classes/", views.classes, name="classes"),
    path("admin-panel/classes/add/", views.class_add, name="class_add"),
    path("admin-panel/classes/<int:pk>/edit/", views.class_edit, name="class_edit"),
    path("admin-panel/classes/<int:pk>/delete/", views.class_delete, name="class_delete"),
    path("admin-panel/subjects/", views.subjects, name="subjects"),
    path("admin-panel/subjects/add/", views.subject_add, name="subject_add"),
    path("admin-panel/subjects/<int:pk>/edit/", views.subject_edit, name="subject_edit"),
    path("admin-panel/subjects/<int:pk>/delete/", views.subject_delete, name="subject_delete"),
    path("admin-panel/assignments/", views.assignments, name="assignments"),
    path("admin-panel/assignments/add/", views.assignment_add, name="assignment_add"),
    path("admin-panel/assignments/<int:pk>/edit/", views.assignment_edit, name="assignment_edit"),
    path("admin-panel/assignments/<int:pk>/delete/", views.assignment_delete, name="assignment_delete"),
]

from django.urls import path
from . import views
urlpatterns=[
 path("teacher/",views.teacher_result_home,name="teacher_result_home"),
 path("teacher/assignment/<int:assignment_id>/semester/<int:semester_id>/",views.enter_results,name="enter_results"),
 path("admin/",views.admin_results,name="admin_results"),
 path("admin/<int:pk>/approve/",views.approve_result,name="approve_result"),
 path("admin/<int:pk>/reject/",views.reject_result,name="reject_result"),
 path("student/",views.student_results,name="student_results"),
]

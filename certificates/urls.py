from django.urls import path
from . import views

urlpatterns = [
    path("", views.certificate_home, name="certificate_home"),
    path("<int:pk>/save-comment/", views.save_certificate_comment, name="save_certificate_comment"),
    path("<int:pk>/download/", views.download_certificate, name="download_certificate"),
    path("verify/<uuid:token>/", views.verify_certificate, name="verify_certificate"),
]

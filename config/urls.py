from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path("django-admin/", admin.site.urls),
    path("", include("accounts.urls")),
    path("academics/", include("academics.urls")),
    path("students/", include("students.urls")),
    path("teachers/", include("teachers.urls")),
    path("results/", include("results.urls")),
    path("certificates/", include("certificates.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

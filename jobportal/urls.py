from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path

from jobs import views as job_views

from . import views


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("register/", include("users.urls")),
    path("login/", auth_views.LoginView.as_view(template_name="users/login.html"), name="login"),
    path("logout/", auth_views.LogoutView.as_view(next_page="home"), name="logout"),
    path("users/", include("users.urls")),
    path("jobs/", include("jobs.urls")),
    path("job/<int:id>/", job_views.job_detail, name="job_detail"),
    path("apply/<int:job_id>/", job_views.apply_job, name="apply_job"),
    path("save/<int:job_id>/", job_views.toggle_save_job, name="toggle_save_job"),
    path("dashboard/", job_views.dashboard, name="dashboard"),
    path("saved-jobs/", job_views.saved_jobs, name="saved_jobs"),
    path("application-success/", job_views.application_success, name="application_success"),
    path("visit-company/<int:id>/", job_views.visit_company, name="visit_company"),
    path("hr/dashboard/", job_views.hr_dashboard, name="hr_dashboard"),
    path("hr/applications/<int:application_id>/", job_views.hr_application_review, name="hr_application_review"),
    path("interview/<int:application_id>/", job_views.interview, name="interview"),
    path("interview-report/<int:application_id>/", job_views.interview_report, name="interview_report_root"),
    path(
        "interview-report/<int:application_id>/download/",
        job_views.download_interview_report,
        name="download_interview_report_root",
    ),
    path("accounts/", include("allauth.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

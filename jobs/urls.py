from django.urls import path

from . import views


urlpatterns = [
    path("", views.job_list, name="job_list"),
    path("category/<slug:category>/", views.category_jobs, name="category_jobs"),
    path("save/<int:job_id>/", views.toggle_save_job, name="toggle_save_job_legacy"),
    path("<int:id>/", views.job_detail, name="job_detail_legacy"),
    path("visit-company/<int:id>/", views.visit_company, name="visit_company_legacy"),
    path("apply/<int:job_id>/", views.apply_job, name="apply_job_legacy"),
    path("dashboard/", views.dashboard, name="dashboard_legacy"),
    path("saved-jobs/", views.saved_jobs, name="saved_jobs_legacy"),
    path("application-success/", views.application_success, name="application_success_legacy"),
    path("delete-application/<int:id>/", views.delete_application, name="delete_application"),
    path("hr-dashboard/", views.hr_dashboard, name="hr_dashboard_legacy"),
    path("hr/applications/<int:application_id>/", views.hr_application_review, name="hr_application_review_legacy"),
    path("update-status/<int:app_id>/<str:status>/", views.update_status, name="update_status"),
    path("admin-dashboard/", views.admin_dashboard, name="admin_dashboard"),
    path("interview/<int:application_id>/", views.interview, name="interview_legacy"),
    path("start-interview/", views.start_interview, name="start_interview"),
    path("finish-interview/<int:application_id>/", views.finish_interview, name="finish_interview"),
    path("interview-report/<int:application_id>/", views.interview_report, name="interview_report"),
    path(
        "interview-report/<int:application_id>/download/",
        views.download_interview_report,
        name="download_interview_report",
    ),
]

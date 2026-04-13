from django.contrib import admin

from .models import Application, ApplicationTimeline, Job, SavedJob


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "company",
        "category",
        "role",
        "location",
        "job_type",
        "salary",
        "views_count",
        "website_clicks",
        "created_at",
    )
    list_filter = ("category", "job_type", "location", "created_at")
    search_fields = (
        "title",
        "company",
        "role",
        "department",
        "industry_type",
        "location",
        "skills_required",
    )
    readonly_fields = ("views_count", "website_clicks", "created_at")
    ordering = ("-created_at",)


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = (
        "full_name",
        "job",
        "status",
        "match_percentage",
        "resume_score",
        "interview_score",
        "final_score",
        "applied_at",
    )
    list_filter = ("status", "job__company", "job__category", "applied_at")
    search_fields = ("full_name", "email", "job__title", "job__company", "skills")
    autocomplete_fields = ("user", "job")


@admin.register(ApplicationTimeline)
class ApplicationTimelineAdmin(admin.ModelAdmin):
    list_display = ("application", "status", "actor", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("application__full_name", "application__job__title", "note")


@admin.register(SavedJob)
class SavedJobAdmin(admin.ModelAdmin):
    list_display = ("user", "job", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user__username", "job__title", "job__company")

from django.contrib.auth.models import User
from django.db import models


INTERVIEW_TYPE = [
    ("online", "Online Interview"),
]


class Job(models.Model):
    CATEGORY_CHOICES = [
        ("it", "IT / Software Jobs"),
        ("data-science", "Data Science / AI Jobs"),
        ("marketing", "Marketing Jobs"),
        ("finance", "Finance Jobs"),
        ("design", "Design Jobs"),
        ("mobile-app-development", "Mobile App Development"),
    ]

    JOB_TYPE_CHOICES = [
        ("Full Time", "Full Time"),
        ("Part Time", "Part Time"),
        ("Internship", "Internship"),
        ("Remote", "Remote"),
    ]

    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    category = models.CharField(max_length=40, choices=CATEGORY_CHOICES, default="it")
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    job_type = models.CharField(max_length=50, choices=JOB_TYPE_CHOICES)
    salary = models.CharField(max_length=100, blank=True, null=True)
    industry_type = models.CharField(max_length=200, blank=True, null=True)
    department = models.CharField(max_length=200, blank=True, null=True)
    role = models.CharField(max_length=200, blank=True, null=True)
    role_category = models.CharField(max_length=200, blank=True, null=True)
    employment_type = models.CharField(max_length=200, blank=True, null=True)
    education = models.TextField(blank=True, null=True)
    interview_type = models.CharField(max_length=10, choices=INTERVIEW_TYPE, default="online")
    description = models.TextField()
    skills_required = models.TextField(help_text="Comma separated skills")
    experience_required = models.CharField(max_length=100, blank=True, null=True)
    about_company = models.TextField(blank=True, null=True)
    company_website = models.URLField(blank=True, null=True)
    company_logo = models.ImageField(upload_to="company_logos/", blank=True, null=True)
    views_count = models.IntegerField(default=0)
    website_clicks = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.company}"

    def get_skills_list(self):
        if not self.skills_required:
            return []
        return [skill.strip() for skill in self.skills_required.split(",") if skill.strip()]


class Application(models.Model):
    class Status(models.TextChoices):
        APPLIED = "Applied", "Applied"
        UNDER_REVIEW = "Under Review", "Under Review"
        INTERVIEW_SCHEDULED = "Interview Scheduled", "Interview Scheduled"
        INTERVIEW_COMPLETED = "Interview Completed", "Interview Completed"
        SELECTED = "Selected", "Selected"
        REJECTED = "Rejected", "Rejected"

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="applications")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="applications")
    full_name = models.CharField(max_length=255, blank=True, default="")
    email = models.EmailField(blank=True, default="")
    phone_number = models.CharField(max_length=20, blank=True, default="")
    resume = models.FileField(upload_to="resumes/")
    skills = models.TextField(blank=True)
    cover_letter = models.TextField(blank=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.APPLIED)
    interview_type = models.CharField(
        max_length=20,
        choices=[("Online", "Online")],
        default="Online",
    )
    interview_date = models.DateTimeField(blank=True, null=True)
    interview_link = models.CharField(max_length=255, blank=True)
    hr_notes = models.TextField(blank=True)
    matched_skills = models.TextField(blank=True)
    missing_skills = models.TextField(blank=True)
    match_score = models.FloatField(default=0)
    match_percentage = models.FloatField(default=0)
    resume_score = models.FloatField(default=0)
    technical_score = models.FloatField(default=0)
    communication_score = models.FloatField(default=0)
    confidence_score = models.FloatField(default=0)
    interview_score = models.FloatField(default=0)
    overall_score = models.FloatField(default=0)
    final_score = models.FloatField(default=0)
    salary_suggestion = models.CharField(max_length=120, blank=True)
    ai_summary = models.TextField(blank=True)
    generated_questions = models.JSONField(default=list, blank=True)
    submitted_answers = models.JSONField(default=list, blank=True)
    offer_letter = models.TextField(blank=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-applied_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "job"],
                name="unique_application_per_user_and_job",
            )
        ]

    def __str__(self):
        return f"{self.user.username} - {self.job.title} - {self.status}"


class ApplicationTimeline(models.Model):
    application = models.ForeignKey(
        Application,
        on_delete=models.CASCADE,
        related_name="timeline_events",
    )
    status = models.CharField(max_length=30)
    note = models.TextField(blank=True)
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="application_timeline_events",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.application} -> {self.status}"


class SavedJob(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="saved_jobs")
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name="saved_by_users")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "job"],
                name="unique_saved_job_per_user",
            )
        ]

    def __str__(self):
        return f"{self.user.username} saved {self.job.title}"

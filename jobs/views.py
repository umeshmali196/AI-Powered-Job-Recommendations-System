from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.core.mail import send_mail
from django.db.models import Avg, Count, Q
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from users.forms import CandidateProfileForm, ProfilePhotoForm
from users.models import Profile
from users.social import get_github_account, sync_github_profile

from .forms import HRApplicationUpdateForm, JobApplicationForm
from .models import Application, ApplicationTimeline, Job, SavedJob
from .utils import (
    build_offer_letter,
    calculate_final_score,
    calculate_profile_completion,
    calculate_resume_insights,
    calculate_semantic_match,
    evaluate_interview,
    extract_text_from_resume,
    get_profile_completion_checks,
    generate_interview_questions,
    recommend_jobs_for_profile,
    suggest_salary,
)


JOB_CATEGORY_RULES = [
    {
        "name": "IT / Software Jobs",
        "slug": "it",
        "icon": "fas fa-laptop-code",
        "description": "Software engineering, web development, QA, DevOps, and cloud roles.",
    },
    {
        "name": "Data Science / AI Jobs",
        "slug": "data-science",
        "icon": "fas fa-brain",
        "description": "Data science, machine learning, analytics, and AI-focused careers.",
    },
    {
        "name": "Marketing Jobs",
        "slug": "marketing",
        "icon": "fas fa-bullhorn",
        "description": "Growth, digital marketing, branding, and content opportunities.",
    },
    {
        "name": "Finance Jobs",
        "slug": "finance",
        "icon": "fas fa-chart-line",
        "description": "Accounting, financial analysis, payroll, tax, and banking roles.",
    },
    {
        "name": "Design Jobs",
        "slug": "design",
        "icon": "fas fa-pen-ruler",
        "description": "UI/UX, product, visual, and graphic design openings.",
    },
    {
        "name": "Mobile App Development",
        "slug": "mobile-app-development",
        "icon": "fas fa-mobile-screen-button",
        "description": "Android, iOS, Flutter, React Native, and cross-platform app roles.",
    },
]

CATEGORY_LOOKUP = {category["slug"]: category for category in JOB_CATEGORY_RULES}

JOB_ROLE_DEFAULTS = {
    "it": {
        "industry_type": "IT Services & Consulting",
        "department": "Engineering / Software Development",
        "role": "Software Developer / Engineer",
        "role_category": "Software Development",
        "education": "B.Tech, B.E., BCA, MCA, or a related computer science discipline.",
    },
    "data-science": {
        "industry_type": "Data Science, Analytics & AI",
        "department": "Data Science & Analytics",
        "role": "Data Analyst / Machine Learning Professional",
        "role_category": "Data & AI",
        "education": "B.Tech, B.Sc, M.Sc, or equivalent background in CS, Statistics, Mathematics, or Data Science.",
    },
    "marketing": {
        "industry_type": "Advertising, Media & Digital Marketing",
        "department": "Marketing & Growth",
        "role": "Digital Marketing / Brand Growth Specialist",
        "role_category": "Marketing",
        "education": "Bachelor's degree in Marketing, Business, Commerce, or a related discipline.",
    },
    "finance": {
        "industry_type": "Financial Services & Consulting",
        "department": "Finance, Accounts & Operations",
        "role": "Financial Analyst / Accounts Professional",
        "role_category": "Finance Operations",
        "education": "B.Com, M.Com, MBA Finance, CA Inter, or related commerce and finance qualifications.",
    },
    "design": {
        "industry_type": "Product Design & Creative Services",
        "department": "Design & User Experience",
        "role": "UI/UX Designer / Graphic Designer",
        "role_category": "Design",
        "education": "Bachelor's degree in Design, Fine Arts, Multimedia, or equivalent portfolio-based experience.",
    },
    "mobile-app-development": {
        "industry_type": "Mobile Products & Application Development",
        "department": "Mobile Engineering",
        "role": "Android / iOS / Flutter Developer",
        "role_category": "Mobile Development",
        "education": "B.Tech, B.E., BCA, MCA, or a related software and mobile application background.",
    },
}

LEGACY_STATUS_MAP = {
    "Pending": Application.Status.APPLIED,
    "Reviewed": Application.Status.UNDER_REVIEW,
    "Shortlisted": Application.Status.UNDER_REVIEW,
    "Rejected": Application.Status.REJECTED,
}


def build_role_details(job):
    defaults = JOB_ROLE_DEFAULTS.get(job.category, JOB_ROLE_DEFAULTS["it"])
    employment_type = job.employment_type
    if not employment_type:
        if job.job_type == "Full Time":
            employment_type = "Full Time, Permanent"
        elif job.job_type == "Part Time":
            employment_type = "Part Time"
        elif job.job_type == "Internship":
            employment_type = "Internship"
        else:
            employment_type = job.job_type

    return [
        {"label": "Industry Type", "value": job.industry_type or defaults["industry_type"]},
        {"label": "Department", "value": job.department or defaults["department"]},
        {"label": "Role", "value": job.role or job.title or defaults["role"]},
        {"label": "Role Category", "value": job.role_category or defaults["role_category"]},
        {"label": "Employment Type", "value": employment_type},
        {"label": "Education", "value": job.education or defaults["education"]},
    ]


def get_saved_job_ids(request):
    if not request.user.is_authenticated:
        return set()
    return set(SavedJob.objects.filter(user=request.user).values_list("job_id", flat=True))


def mark_saved_jobs(jobs, saved_job_ids):
    for job in jobs:
        job.is_saved = job.id in saved_job_ids
    return jobs


def attach_match_percentages(request, jobs):
    jobs = list(jobs)
    if not request.user.is_authenticated:
        for job in jobs:
            job.match_percentage = 0
        return jobs

    profile = getattr(request.user, "profile", None)
    if not profile:
        for job in jobs:
            job.match_percentage = 0
        return jobs

    return recommend_jobs_for_profile(request.user, profile, jobs, limit=len(jobs))


def record_timeline(application, status, note="", actor=None):
    ApplicationTimeline.objects.create(
        application=application,
        status=status,
        note=note,
        actor=actor,
    )


def build_profile_actions(user, profile):
    action_meta = {
        "resume": {
            "description": "Resume unlocks stronger AI matching and score analysis.",
            "icon": "fa-solid fa-file-arrow-up",
        },
        "skills": {
            "description": "List your tools, languages, and strengths for better recommendations.",
            "icon": "fa-solid fa-lightbulb",
        },
        "summary": {
            "description": "A short summary helps recruiters understand your background quickly.",
            "icon": "fa-solid fa-align-left",
        },
        "headline": {
            "description": "Show the role or direction you want recruiters to notice.",
            "icon": "fa-solid fa-id-badge",
        },
        "preferred_location": {
            "description": "Location preferences help the portal surface more relevant roles.",
            "icon": "fa-solid fa-location-dot",
        },
        "phone_number": {
            "description": "Recruiters can contact you faster when your phone number is present.",
            "icon": "fa-solid fa-phone",
        },
        "email": {
            "description": "Keep your email updated so interview and status alerts reach you.",
            "icon": "fa-solid fa-envelope",
        },
        "name": {
            "description": "A complete name makes your profile look more polished and professional.",
            "icon": "fa-solid fa-user",
        },
        "profile_photo": {
            "description": "A profile photo gives your dashboard and profile a complete identity.",
            "icon": "fa-solid fa-camera",
        },
        "github_username": {
            "description": "GitHub adds extra signal for tech and developer roles.",
            "icon": "fa-brands fa-github",
        },
    }

    profile_checks = []
    for check in get_profile_completion_checks(user, profile):
        meta = action_meta.get(check["key"], {})
        profile_checks.append(
            {
                "done": check["done"],
                "title": check["label"],
                "description": meta.get("description", ""),
                "boost": check["weight"],
                "icon": meta.get("icon", "fa-solid fa-circle"),
            }
        )

    missing_actions = [item for item in profile_checks if not item["done"]]
    return missing_actions[:3], len(missing_actions)


def parse_profile_skills(profile):
    if not profile.skills:
        return []
    return [skill.strip() for skill in profile.skills.split(",") if skill.strip()]


def build_interview_link(request, application):
    link = application.interview_link or reverse("interview", args=[application.id])
    if link.startswith("http://") or link.startswith("https://"):
        return link
    return request.build_absolute_uri(link)


def send_application_confirmation(application):
    send_mail(
        subject=f"Application received for {application.job.title}",
        message=(
            f"Hi {application.full_name},\n\n"
            f"Your application for {application.job.title} at {application.job.company} "
            f"has been submitted successfully.\n\n"
            f"Current status: {application.status}\n"
            f"Match score: {application.match_percentage}%\n"
            f"Resume score: {application.resume_score}%\n"
        ),
        from_email=None,
        recipient_list=[application.email],
        fail_silently=True,
    )


def send_interview_invitation(request, application):
    send_mail(
        subject=f"Interview scheduled for {application.job.title}",
        message=(
            f"Hi {application.full_name},\n\n"
            f"Your interview for {application.job.title} at {application.job.company} is scheduled for "
            f"{application.interview_date:%d %b %Y %I:%M %p}.\n"
            f"Interview link: {build_interview_link(request, application)}\n\n"
            f"Please keep your camera on and stay visible during the AI interview round."
        ),
        from_email=None,
        recipient_list=[application.email],
        fail_silently=True,
    )


def send_final_decision_email(application):
    if application.status == Application.Status.SELECTED:
        subject = f"Offer update for {application.job.title}"
        message = (
            f"Hi {application.full_name},\n\n"
            f"Congratulations. You have been selected for {application.job.title} at {application.job.company}.\n\n"
            f"{application.offer_letter}"
        )
    else:
        subject = f"Application update for {application.job.title}"
        message = (
            f"Hi {application.full_name},\n\n"
            f"Thank you for interviewing for {application.job.title} at {application.job.company}. "
            f"Your application status has been updated to {application.status}."
        )

    send_mail(subject=subject, message=message, from_email=None, recipient_list=[application.email], fail_silently=True)


def enrich_jobs_with_application_status(user, jobs):
    status_map = {
        application.job_id: application.status
        for application in Application.objects.filter(user=user).only("job_id", "status")
    }
    for job in jobs:
        job.application_status = status_map.get(job.id)
    return jobs


def job_list(request):
    category_counts = {
        item["category"]: item["total"]
        for item in Job.objects.values("category").annotate(total=Count("id"))
    }
    job_categories = []
    for category in JOB_CATEGORY_RULES:
        category_data = category.copy()
        category_data["count"] = category_counts.get(category["slug"], 0)
        job_categories.append(category_data)

    featured_jobs = attach_match_percentages(request, Job.objects.all()[:6])
    saved_job_ids = get_saved_job_ids(request)
    mark_saved_jobs(featured_jobs, saved_job_ids)
    if request.user.is_authenticated:
        enrich_jobs_with_application_status(request.user, featured_jobs)

    return render(
        request,
        "jobs/job_list.html",
        {
            "job_categories": job_categories,
            "featured_jobs": featured_jobs,
            "total_jobs": Job.objects.count(),
            "total_categories": len(JOB_CATEGORY_RULES),
        },
    )


def category_jobs(request, category):
    if category not in CATEGORY_LOOKUP:
        raise Http404("Category not found")

    search_query = request.GET.get("q", "").strip()
    location_query = request.GET.get("location", "").strip()
    job_type_query = request.GET.get("job_type", "").strip()

    jobs_queryset = Job.objects.filter(category=category)
    if search_query:
        jobs_queryset = jobs_queryset.filter(
            Q(title__icontains=search_query)
            | Q(company__icontains=search_query)
            | Q(skills_required__icontains=search_query)
            | Q(description__icontains=search_query)
        )
    if location_query:
        jobs_queryset = jobs_queryset.filter(location__icontains=location_query)
    if job_type_query:
        jobs_queryset = jobs_queryset.filter(job_type=job_type_query)

    jobs = attach_match_percentages(request, jobs_queryset)
    saved_job_ids = get_saved_job_ids(request)
    mark_saved_jobs(jobs, saved_job_ids)
    if request.user.is_authenticated:
        enrich_jobs_with_application_status(request.user, jobs)

    return render(
        request,
        "jobs/category_jobs.html",
        {
            "jobs": jobs,
            "selected_category": CATEGORY_LOOKUP[category],
            "job_categories": JOB_CATEGORY_RULES,
            "search_query": search_query,
            "location_query": location_query,
            "job_type_query": job_type_query,
            "job_type_choices": Job.JOB_TYPE_CHOICES,
            "results_count": len(jobs),
        },
    )


def job_detail(request, id):
    job = get_object_or_404(Job, id=id)
    job.views_count += 1
    job.save(update_fields=["views_count"])

    saved_job_ids = get_saved_job_ids(request)
    job.is_saved = job.id in saved_job_ids
    similar_jobs = attach_match_percentages(
        request,
        Job.objects.filter(category=job.category).exclude(id=job.id)[:3],
    )
    mark_saved_jobs(similar_jobs, saved_job_ids)
    if request.user.is_authenticated:
        enrich_jobs_with_application_status(request.user, similar_jobs)

    existing_application = None
    job_match = None
    if request.user.is_authenticated:
        existing_application = Application.objects.filter(user=request.user, job=job).first()
        profile = request.user.profile
        resume_text = extract_text_from_resume(profile.resume.path) if profile.resume else ""
        if profile.resume:
            job_match = calculate_resume_insights(request.user, profile, job, resume_text)

    return render(
        request,
        "jobs/job_detail.html",
        {
            "job": job,
            "similar_jobs": similar_jobs,
            "role_details": build_role_details(job),
            "existing_application": existing_application,
            "job_match": job_match,
        },
    )


def visit_company(request, id):
    job = get_object_or_404(Job, id=id)
    job.website_clicks += 1
    job.save(update_fields=["website_clicks"])
    return redirect(job.company_website)


@login_required
def apply_job(request, job_id):
    job = get_object_or_404(Job, id=job_id)
    profile = request.user.profile

    if Application.objects.filter(user=request.user, job=job).exists():
        messages.info(request, "You have already applied for this role.")
        return redirect("job_detail", id=job.id)

    if request.method == "POST":
        form = JobApplicationForm(request.POST, request.FILES, user=request.user, profile=profile)
        if form.is_valid():
            uploaded_resume = form.cleaned_data.get("resume")
            if uploaded_resume:
                profile.resume = uploaded_resume
                profile.save()

            resume_file = profile.resume
            resume_text = extract_text_from_resume(resume_file.path) if resume_file else ""
            insights = calculate_resume_insights(request.user, profile, job, resume_text)

            application = form.save(commit=False)
            application.user = request.user
            application.job = job
            application.resume = resume_file
            application.status = Application.Status.APPLIED
            application.match_score = insights["semantic_score"]
            application.match_percentage = insights["match_percentage"]
            application.resume_score = insights["resume_score"]
            application.matched_skills = ", ".join(insights["matched_skills"])
            application.missing_skills = ", ".join(insights["missing_skills"])
            application.ai_summary = insights["summary"]
            application.overall_score = round(
                (application.resume_score * 0.45) + (application.match_percentage * 0.55),
                2,
            )
            application.final_score = application.overall_score
            application.salary_suggestion = suggest_salary(application)
            application.save()

            if form.cleaned_data.get("phone_number") and profile.phone_number != form.cleaned_data["phone_number"]:
                profile.phone_number = form.cleaned_data["phone_number"]
            if form.cleaned_data.get("skills"):
                profile.skills = form.cleaned_data["skills"]
            profile.save()

            record_timeline(
                application,
                Application.Status.APPLIED,
                note="Application submitted by candidate.",
                actor=request.user,
            )
            send_application_confirmation(application)
            request.session["last_application_id"] = application.id
            messages.success(request, "Application submitted successfully.")
            return redirect("application_success")
    else:
        form = JobApplicationForm(user=request.user, profile=profile)

    return render(
        request,
        "jobs/apply.html",
        {
            "job": job,
            "form": form,
            "previous_resume": profile.resume,
        },
    )


@login_required
def application_success(request):
    application_id = request.GET.get("application_id") or request.session.get("last_application_id")
    if not application_id:
        return redirect("dashboard")

    application = get_object_or_404(
        Application.objects.select_related("job"),
        id=application_id,
        user=request.user,
    )
    return render(request, "jobs/application_success.html", {"application": application})


@login_required
def toggle_save_job(request, job_id):
    if request.method != "POST":
        raise Http404("Invalid request method")

    job = get_object_or_404(Job, id=job_id)
    saved_job, created = SavedJob.objects.get_or_create(user=request.user, job=job)
    if created:
        messages.success(request, f"{job.title} added to your saved jobs.")
    else:
        saved_job.delete()
        messages.success(request, f"{job.title} removed from your saved jobs.")

    next_url = request.POST.get("next") or request.GET.get("next") or request.META.get("HTTP_REFERER")
    if next_url:
        return redirect(next_url)
    return redirect("job_detail", id=job.id)


@login_required
def saved_jobs(request):
    saved_jobs_queryset = SavedJob.objects.filter(user=request.user).select_related("job")
    application_status_map = {
        application.job_id: application.status
        for application in Application.objects.filter(user=request.user).only("job_id", "status")
    }
    saved_jobs_list = list(saved_jobs_queryset)
    for saved_job in saved_jobs_list:
        saved_job.application_status = application_status_map.get(saved_job.job_id)
        saved_job.job.is_saved = True

    return render(request, "jobs/saved_jobs.html", {"saved_jobs": saved_jobs_list})


@login_required
def dashboard(request):
    profile = request.user.profile
    github_account = get_github_account(request.user)
    if github_account:
        sync_github_profile(profile, github_account)

    if request.method == "POST":
        if "photo_submit" in request.POST:
            photo_form = ProfilePhotoForm(request.POST, request.FILES, instance=profile)
            profile_form = CandidateProfileForm(instance=profile, user=request.user)
            if photo_form.is_valid():
                photo_form.save()
                messages.success(request, "Profile photo updated successfully.")
                return redirect("dashboard")
        else:
            profile_form = CandidateProfileForm(request.POST, request.FILES, instance=profile, user=request.user)
            photo_form = ProfilePhotoForm(instance=profile)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Profile updated successfully.")
                return redirect("dashboard")
    else:
        profile_form = CandidateProfileForm(instance=profile, user=request.user)
        photo_form = ProfilePhotoForm(instance=profile)

    applications = list(
        Application.objects.filter(user=request.user)
        .select_related("job")
        .prefetch_related("timeline_events")
    )
    saved_jobs_list = list(SavedJob.objects.filter(user=request.user).select_related("job"))
    saved_job_ids = {item.job_id for item in saved_jobs_list}

    recommended_jobs = recommend_jobs_for_profile(request.user, profile, Job.objects.all(), limit=6)
    mark_saved_jobs(recommended_jobs, saved_job_ids)
    enrich_jobs_with_application_status(request.user, recommended_jobs)

    status_counts = {
        status: 0
        for status, _ in Application.Status.choices
    }
    for application in applications:
        status_counts[application.status] = status_counts.get(application.status, 0) + 1

    application_status_map = {application.job_id: application.status for application in applications}
    for saved_job in saved_jobs_list:
        saved_job.application_status = application_status_map.get(saved_job.job_id)
        saved_job.job.is_saved = True

    total_applications = len(applications)
    average_match = round(
        Application.objects.filter(user=request.user).aggregate(value=Avg("match_percentage"))["value"] or 0,
        2,
    )
    average_resume_score = round(
        Application.objects.filter(user=request.user).aggregate(value=Avg("resume_score"))["value"] or 0,
        2,
    )
    top_match = max(applications, key=lambda app: app.match_percentage, default=None)
    profile_completion = calculate_profile_completion(request.user, profile)
    profile_actions, missing_profile_count = build_profile_actions(request.user, profile)
    profile_skills = parse_profile_skills(profile)
    recent_events = ApplicationTimeline.objects.filter(application__user=request.user).select_related("application", "application__job")[:6]
    upcoming_interview = (
        Application.objects.filter(user=request.user, status=Application.Status.INTERVIEW_SCHEDULED)
        .exclude(interview_date__isnull=True)
        .order_by("interview_date")
        .select_related("job")
        .first()
    )

    context = {
        "profile": profile,
        "profile_form": profile_form,
        "photo_form": photo_form,
        "github_account": github_account,
        "applications": applications,
        "saved_jobs": saved_jobs_list,
        "recommended_jobs": recommended_jobs,
        "total_applications": total_applications,
        "average_match": average_match,
        "average_resume_score": average_resume_score,
        "top_match": top_match,
        "profile_completion": profile_completion,
        "profile_actions": profile_actions,
        "missing_profile_count": missing_profile_count,
        "profile_skills": profile_skills,
        "resume_score": round(top_match.resume_score, 2) if top_match else average_resume_score,
        "status_counts": status_counts,
        "applied_count": status_counts.get(Application.Status.APPLIED, 0),
        "under_review_count": status_counts.get(Application.Status.UNDER_REVIEW, 0),
        "interview_scheduled_count": status_counts.get(Application.Status.INTERVIEW_SCHEDULED, 0),
        "interview_completed_count": status_counts.get(Application.Status.INTERVIEW_COMPLETED, 0),
        "selected_count": status_counts.get(Application.Status.SELECTED, 0),
        "rejected_count": status_counts.get(Application.Status.REJECTED, 0),
        "recent_events": recent_events,
        "upcoming_interview": upcoming_interview,
    }
    return render(request, "users/dashboard.html", context)


@login_required
def delete_application(request, id):
    application = get_object_or_404(Application, id=id, user=request.user)
    application.delete()
    messages.success(request, "Application withdrawn.")
    return redirect("dashboard")


@staff_member_required
def hr_dashboard(request):
    status_filter = request.GET.get("status", "").strip()
    applications = Application.objects.select_related("user", "job").order_by("-applied_at")
    if status_filter:
        applications = applications.filter(status=status_filter)

    metrics = {
        "total": Application.objects.count(),
        "applied": Application.objects.filter(status=Application.Status.APPLIED).count(),
        "under_review": Application.objects.filter(status=Application.Status.UNDER_REVIEW).count(),
        "interview_scheduled": Application.objects.filter(status=Application.Status.INTERVIEW_SCHEDULED).count(),
        "selected": Application.objects.filter(status=Application.Status.SELECTED).count(),
        "rejected": Application.objects.filter(status=Application.Status.REJECTED).count(),
        "average_match": round(Application.objects.aggregate(value=Avg("match_percentage"))["value"] or 0, 2),
    }
    top_candidates = Application.objects.select_related("user", "job").order_by(
        "-final_score",
        "-interview_score",
        "-match_percentage",
    )[:6]

    return render(
        request,
        "jobs/hr_dashboard.html",
        {
            "applications": applications,
            "metrics": metrics,
            "top_candidates": top_candidates,
            "status_choices": Application.Status.choices,
            "active_status": status_filter,
        },
    )


@staff_member_required
def hr_application_review(request, application_id):
    application = get_object_or_404(
        Application.objects.select_related("user", "job"),
        id=application_id,
    )
    previous_status = application.status

    if request.method == "POST":
        form = HRApplicationUpdateForm(request.POST, instance=application)
        if form.is_valid():
            application = form.save(commit=False)
            if application.status == Application.Status.SELECTED and not application.offer_letter:
                application.final_score = calculate_final_score(application)
                application.salary_suggestion = suggest_salary(application)
                application.offer_letter = build_offer_letter(application)
            application.save()

            note = application.hr_notes or "Status updated by HR."
            if application.status != previous_status:
                record_timeline(application, application.status, note=note, actor=request.user)
                if application.status == Application.Status.INTERVIEW_SCHEDULED:
                    send_interview_invitation(request, application)
                if application.status in {Application.Status.SELECTED, Application.Status.REJECTED}:
                    if application.status == Application.Status.SELECTED and not application.offer_letter:
                        application.offer_letter = build_offer_letter(application)
                        application.save(update_fields=["offer_letter"])
                    send_final_decision_email(application)

            messages.success(request, "Application review updated.")
            return redirect("hr_application_review", application_id=application.id)
    else:
        form = HRApplicationUpdateForm(instance=application)

    if not application.generated_questions:
        application.generated_questions = generate_interview_questions(application)
        application.save(update_fields=["generated_questions"])

    return render(
        request,
        "jobs/hr_application_review.html",
        {
            "application": application,
            "form": form,
            "timeline": application.timeline_events.all(),
        },
    )


def get_application_for_interview(request, application_id):
    queryset = Application.objects.select_related("job", "user")
    if request.user.is_staff:
        return get_object_or_404(queryset, id=application_id)
    return get_object_or_404(queryset, id=application_id, user=request.user)


@login_required
def interview(request, application_id):
    application = get_application_for_interview(request, application_id)

    if not application.generated_questions:
        application.generated_questions = generate_interview_questions(application)
        application.save(update_fields=["generated_questions"])

    if request.method == "POST":
        answers = []
        for question in application.generated_questions:
            answers.append(request.POST.get(f"answer_{question['id']}", ""))

        evaluation = evaluate_interview(application, answers)
        application.submitted_answers = evaluation["answers"]
        application.technical_score = evaluation["technical_score"]
        application.communication_score = evaluation["communication_score"]
        application.confidence_score = evaluation["confidence_score"]
        application.interview_score = evaluation["overall_score"]
        application.overall_score = evaluation["overall_score"]
        application.final_score = calculate_final_score(application)
        application.salary_suggestion = suggest_salary(application)
        application.ai_summary = evaluation["summary"]
        if application.status not in {Application.Status.SELECTED, Application.Status.REJECTED}:
            application.status = Application.Status.INTERVIEW_COMPLETED
        application.save()

        record_timeline(
            application,
            Application.Status.INTERVIEW_COMPLETED,
            note="Candidate completed the AI interview round.",
            actor=request.user,
        )
        messages.success(request, "Interview submitted and evaluated successfully.")
        return redirect("interview_report", application_id=application.id)

    return render(request, "interview.html", {"application": application})


@login_required
def interview_report(request, application_id):
    application = get_application_for_interview(request, application_id)
    return render(request, "jobs/interview_report.html", {"application": application})


@login_required
def download_interview_report(request, application_id):
    application = get_application_for_interview(request, application_id)
    report = (
        f"Interview Report\n\n"
        f"Candidate: {application.full_name}\n"
        f"Email: {application.email}\n"
        f"Job: {application.job.title}\n"
        f"Company: {application.job.company}\n"
        f"Resume Score: {application.resume_score}%\n"
        f"Match Percentage: {application.match_percentage}%\n"
        f"Technical Score: {application.technical_score}%\n"
        f"Communication Score: {application.communication_score}%\n"
        f"Confidence Score: {application.confidence_score}%\n"
        f"Interview Score: {application.interview_score}%\n"
        f"Final Score: {application.final_score}%\n"
        f"Salary Suggestion: {application.salary_suggestion}\n"
        f"Summary: {application.ai_summary}\n"
    )
    response = HttpResponse(report, content_type="text/plain")
    response["Content-Disposition"] = f'attachment; filename="interview-report-{application.id}.txt"'
    return response


@login_required
def finish_interview(request, application_id):
    return redirect("interview_report", application_id=application_id)


@login_required
def start_interview(request):
    application_id = request.GET.get("application_id")
    if not application_id:
        return redirect("dashboard")
    return redirect("interview", application_id=application_id)


@staff_member_required
def update_status(request, app_id, status):
    application = get_object_or_404(Application, id=app_id)
    normalized_status = LEGACY_STATUS_MAP.get(status, status)
    valid_statuses = {choice[0] for choice in Application.Status.choices}
    if normalized_status not in valid_statuses:
        raise Http404("Invalid status")

    application.status = normalized_status
    application.save(update_fields=["status"])
    record_timeline(application, normalized_status, note="Status updated from quick action.", actor=request.user)
    messages.success(request, "Application status updated.")
    next_url = request.GET.get("next") or request.META.get("HTTP_REFERER")
    if next_url:
        return redirect(next_url)
    return redirect("hr_dashboard")


@staff_member_required
def admin_dashboard(request):
    return redirect("hr_dashboard")


def login_view(request):
    if request.method == "POST":
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect("job_list")
        return render(request, "login.html", {"error": "Invalid credentials"})
    return render(request, "login.html")

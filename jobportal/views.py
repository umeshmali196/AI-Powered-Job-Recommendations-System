from django.shortcuts import render

from jobs.models import Application, Job


def home(request):
    context = {
        "total_jobs": Job.objects.count(),
        "companies_count": Job.objects.values("company").distinct().count(),
        "candidates_count": Application.objects.values("user").distinct().count(),
        "placements_count": Application.objects.filter(status=Application.Status.SELECTED).count(),
    }
    return render(request, "home.html", context)

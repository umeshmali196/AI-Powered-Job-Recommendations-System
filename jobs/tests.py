from django.test import TestCase
from django.urls import reverse

from .models import Job


class JobCategoryTests(TestCase):
    def test_job_detail_shows_role_details_section(self):
        job = Job.objects.create(
            title="Python Developer",
            company="AppWorks",
            location="Pune",
            category="it",
            job_type="Full Time",
            description="Build Django web applications.",
            skills_required="Python, Django, APIs",
        )

        response = self.client.get(reverse('job_detail', args=[job.id]))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Role Details")
        self.assertContains(response, "Industry Type")
        self.assertContains(response, "IT Services &amp; Consulting")

    def test_category_page_filters_by_search_and_location(self):
        matching_job = Job.objects.create(
            title="Python Developer",
            company="AppWorks",
            location="Pune",
            category="it",
            job_type="Full Time",
            description="Build Django web applications.",
            skills_required="Python, Django, APIs",
        )
        Job.objects.create(
            title="Frontend Developer",
            company="UI Labs",
            location="Mumbai",
            category="it",
            job_type="Remote",
            description="Build React interfaces.",
            skills_required="React, JavaScript, CSS",
        )

        response = self.client.get(
            reverse('category_jobs', args=['it']),
            {"q": "Python", "location": "Pune"}
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, matching_job.title)
        self.assertContains(response, "1 jobs found")
        self.assertNotContains(response, "Frontend Developer")

    def test_category_jobs_page_shows_only_selected_category_jobs(self):
        it_job = Job.objects.create(
            title="Python Developer",
            company="AppWorks",
            location="Bengaluru",
            category="it",
            job_type="Full Time",
            description="Build Django web applications.",
            skills_required="Python, Django, APIs",
        )
        data_job = Job.objects.create(
            title="Data Scientist",
            company="Insight Labs",
            location="Hyderabad",
            category="data-science",
            job_type="Full Time",
            description="Create machine learning models for analytics workflows.",
            skills_required="Python, TensorFlow, Machine Learning, Data Science",
        )

        response = self.client.get(reverse('category_jobs', args=['it']))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, it_job.title)
        self.assertNotContains(response, data_job.title)

    def test_unknown_category_returns_404(self):
        response = self.client.get(reverse('category_jobs', args=['unknown-category']))

        self.assertEqual(response.status_code, 404)

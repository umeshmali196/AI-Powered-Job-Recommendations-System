from pathlib import Path

from django import forms

from .models import Application


class JobApplicationForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ["full_name", "email", "phone_number", "resume", "skills", "cover_letter"]
        widgets = {
            "cover_letter": forms.Textarea(attrs={"rows": 5}),
            "skills": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, profile=None, user=None, **kwargs):
        self.profile = profile
        self.user = user
        super().__init__(*args, **kwargs)

        full_name = ""
        if user:
            full_name = user.get_full_name().strip() or user.username
            self.fields["email"].initial = user.email

        if profile:
            self.fields["full_name"].initial = full_name or self.fields["full_name"].initial
            self.fields["phone_number"].initial = profile.phone_number
            self.fields["skills"].initial = profile.skills

        self.fields["resume"].required = False
        for field in self.fields.values():
            field.widget.attrs.setdefault("class", "form-control")

    def clean_resume(self):
        resume = self.cleaned_data.get("resume")
        if not resume:
            return resume

        suffix = Path(resume.name).suffix.lower()
        if suffix != ".pdf":
            raise forms.ValidationError("Please upload your resume as a PDF file.")
        return resume

    def clean(self):
        cleaned_data = super().clean()
        resume = cleaned_data.get("resume")
        existing_resume = getattr(self.profile, "resume", None)
        if not resume and not existing_resume:
            self.add_error("resume", "Upload a PDF resume or add one in your profile first.")
        return cleaned_data


class HRApplicationUpdateForm(forms.ModelForm):
    class Meta:
        model = Application
        fields = ["status", "hr_notes", "interview_date", "interview_link"]
        widgets = {
            "hr_notes": forms.Textarea(attrs={"rows": 4}),
            "interview_date": forms.DateTimeInput(attrs={"type": "datetime-local"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name, field in self.fields.items():
            field.widget.attrs.setdefault(
                "class",
                "form-select" if name == "status" else "form-control",
            )

    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get("status")
        interview_date = cleaned_data.get("interview_date")
        interview_link = (cleaned_data.get("interview_link") or "").strip()

        if status == Application.Status.INTERVIEW_SCHEDULED:
            if not interview_date:
                self.add_error("interview_date", "Select an interview date and time.")
            if not interview_link:
                self.add_error("interview_link", "Add the interview link to notify the candidate.")

        return cleaned_data

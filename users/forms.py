from pathlib import Path

from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from .models import Profile


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField()
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "password1", "password2"]


class CandidateProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=150, required=False)
    last_name = forms.CharField(max_length=150, required=False)
    email = forms.EmailField(required=True)

    class Meta:
        model = Profile
        fields = [
            "first_name",
            "last_name",
            "email",
            "profile_photo",
            "phone_number",
            "headline",
            "preferred_location",
            "skills",
            "summary",
            "resume",
        ]
        widgets = {
            "skills": forms.Textarea(attrs={"rows": 3}),
            "summary": forms.Textarea(attrs={"rows": 4}),
        }

    def __init__(self, *args, user=None, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

        if user:
            self.fields["first_name"].initial = user.first_name
            self.fields["last_name"].initial = user.last_name
            self.fields["email"].initial = user.email

        for name, field in self.fields.items():
            css_class = "form-control"
            if isinstance(field.widget, forms.FileInput):
                css_class = "form-control"
            field.widget.attrs.setdefault("class", css_class)

    def clean_resume(self):
        resume = self.cleaned_data.get("resume")
        if not resume:
            return resume

        suffix = Path(resume.name).suffix.lower()
        if suffix not in {".pdf", ".doc", ".docx"}:
            raise forms.ValidationError("Upload a PDF, DOC, or DOCX resume.")
        return resume

    def clean_profile_photo(self):
        profile_photo = self.cleaned_data.get("profile_photo")
        if not profile_photo:
            return profile_photo

        suffix = Path(profile_photo.name).suffix.lower()
        if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
            raise forms.ValidationError("Upload a JPG, JPEG, PNG, or WEBP profile photo.")
        return profile_photo

    def save(self, commit=True):
        profile = super().save(commit=False)

        if self.user:
            self.user.first_name = self.cleaned_data.get("first_name", "").strip()
            self.user.last_name = self.cleaned_data.get("last_name", "").strip()
            self.user.email = self.cleaned_data["email"]
            if commit:
                self.user.save()

        if commit:
            profile.save()

        return profile


class ProfilePhotoForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["profile_photo"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["profile_photo"].widget.attrs.setdefault("class", "form-control")

    def clean_profile_photo(self):
        profile_photo = self.cleaned_data.get("profile_photo")
        if not profile_photo:
            raise forms.ValidationError("Select a profile photo to upload.")

        suffix = Path(profile_photo.name).suffix.lower()
        if suffix not in {".jpg", ".jpeg", ".png", ".webp"}:
            raise forms.ValidationError("Upload a JPG, JPEG, PNG, or WEBP profile photo.")
        return profile_photo

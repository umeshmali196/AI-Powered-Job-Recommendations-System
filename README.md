# 🤖 AI-Powered Job Recommendation System

An intelligent Django-based job portal that recommends suitable jobs to candidates by analyzing their profile, skills, and resume content. The system supports candidate registration, job discovery, application tracking, AI-based resume matching, online interview evaluation, HR review workflows, and admin-level job/application management.

## 📌 Overview

The AI-Powered Job Recommendation System is designed to make recruitment faster and more data-driven. Candidates can create a profile, upload a resume, browse jobs by category, save jobs, apply for roles, and receive personalized job recommendations. HR/admin users can review applications, schedule interviews, evaluate candidate performance, update application statuses, and generate offer-related information.

The recommendation logic uses resume text extraction, skill matching, TF-IDF vectorization, and cosine similarity to calculate match percentages between candidates and jobs.


## 🚀 Key Features

### 👤 Candidate/User Features


- User registration, login, logout, and profile management
- Candidate dashboard with profile completion score
- Resume upload and profile photo upload
- GitHub profile integration through social authentication
- Browse jobs by category, company, location, job type, and skills
- View detailed job descriptions and company information
- Save and unsave jobs
- Apply for jobs using resume, skills, and cover letter
- AI-based job match percentage and resume score
- Track application status and timeline
- View recommended jobs based on profile and resume
- Attend online interview rounds
- View interview report and final score

### 🧑‍💼 HR/Admin Features

- HR dashboard for application review
- View total applications, status counts, top candidates, and average match score
- Filter applications by status
- Review candidate resume score, match score, interview score, and final score
- Schedule online interviews
- Update application status:
  - Applied
  - Under Review
  - Interview Scheduled
  - Interview Completed
  - Selected
  - Rejected
- Add HR notes
- Generate interview questions
- Evaluate candidate interview answers
- Generate salary suggestion and offer letter for selected candidates
- Manage jobs, applications, saved jobs, and timeline records through Django admin

### 🤖 AI/Recommendation Features

- Resume text extraction from PDF and DOCX files
- Skill extraction and missing skill identification
- TF-IDF based semantic matching between resume and job description
- Candidate profile completion scoring
- Personalized job recommendations
- AI-generated interview questions
- Interview answer evaluation based on:
  - Technical relevance
  - Communication clarity
  - Confidence indicators
- Final candidate score calculation
- Salary suggestion based on job salary and candidate score

## 🖥️ Interfaces

- Home page
- User registration page
- Login/logout pages
- Candidate dashboard
- Job listing page
- Category-wise job listing page
- Job detail page
- Job application page
- Application success page
- Saved jobs page
- Online interview page
- Interview report page
- HR dashboard
- HR application review page
- Django/Jazzmin admin panel

## 🛠️ Technology Stack

| Layer | Technology |
| --- | --- |
| Backend | Python, Django |
| Frontend | HTML, CSS, Bootstrap-style templates, Font Awesome icons |
| Database | SQLite |
| Authentication | Django Auth, Django Allauth |
| Admin UI | Django Jazzmin |
| AI/ML | Scikit-learn TF-IDF, Cosine Similarity |
| Resume Parsing | PyPDF2, DOCX XML extraction |
| Image/File Handling | Pillow, Django Media Files |
| Social Login | Google OAuth, GitHub OAuth |

## 📁 Project Structure

```text
jobportal/
├── jobportal/                  # Main Django project settings and URL routing
│   ├── settings.py
│   ├── urls.py
│   ├── views.py
│   ├── asgi.py
│   └── wsgi.py
├── jobs/                       # Job, application, HR, interview, and recommendation logic
│   ├── models.py               # Job, Application, SavedJob, ApplicationTimeline models
│   ├── views.py                # Job browsing, applying, dashboards, interview flow
│   ├── forms.py                # Application and HR review forms
│   ├── utils.py                # AI matching, resume parsing, interview scoring
│   ├── admin.py
│   └── migrations/
├── users/                      # User profile and registration logic
│   ├── models.py               # Candidate profile model
│   ├── forms.py                # Registration and profile forms
│   ├── views.py
│   ├── social.py               # GitHub profile sync helpers
│   ├── signals.py
│   └── migrations/
├── recommendations/            # Recommendation app placeholder/module
├── templates/                  # HTML templates
│   ├── base.html
│   ├── home.html
│   ├── admin_dashboard.html
│   ├── interview.html
│   ├── interview_result.html
│   ├── jobs/
│   └── users/
├── media/                      # Uploaded resumes, profile photos, company logos
├── db.sqlite3                  # SQLite database for local development
├── manage.py                   # Django management command entry point
└── README.md
```

## 📦 Dependencies

Main Python packages used in this project:

- Django
- django-allauth
- django-jazzmin
- scikit-learn
- scipy
- numpy
- PyPDF2
- Pillow
- requests
- requests-oauthlib
- PyJWT
- cryptography
- opencv-python
- face-recognition
- sentence-transformers
- transformers
- torch

You can generate a full dependency file from the current environment:

```bash
pip freeze > requirements.txt
```

## ⚙️ Installation and Setup

1. Clone the repository:

```bash
git clone https://github.com/your-username/AI-Powered-Job-Recommendations-System.git
cd AI-Powered-Job-Recommendations-System
```

2. Create and activate a virtual environment:

```bash
python -m venv venv
venv\Scripts\activate
```

For macOS/Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

3. Install dependencies:

```bash
pip install -r requirements.txt
```

If `requirements.txt` is not available yet, install the main packages manually:

```bash
pip install django django-allauth django-jazzmin scikit-learn PyPDF2 pillow requests requests-oauthlib
```

4. Apply database migrations:

```bash
python manage.py migrate
```

5. Create a superuser:

```bash
python manage.py createsuperuser
```

6. Run the development server:

```bash
python manage.py runserver
```

7. Open the project in your browser:

```text
http://127.0.0.1:8000/
```

## 🔐 Environment Variables

For GitHub OAuth login, configure these environment variables:

```env
GITHUB_CLIENT_ID=your_github_client_id
GITHUB_CLIENT_SECRET=your_github_client_secret
```

Google login can be configured from the Django admin social application settings when using `django-allauth`.

## 🔗 Main URL Routes

| URL | Description |
| --- | --- |
| `/` | Home page |
| `/register/` | User registration |
| `/login/` | User login |
| `/logout/` | User logout |
| `/jobs/` | Job listing |
| `/jobs/category/<category>/` | Category-wise jobs |
| `/job/<id>/` | Job detail |
| `/apply/<job_id>/` | Apply for a job |
| `/dashboard/` | Candidate dashboard |
| `/saved-jobs/` | Saved jobs |
| `/hr/dashboard/` | HR dashboard |
| `/hr/applications/<id>/` | HR application review |
| `/interview/<application_id>/` | Online interview |
| `/interview-report/<application_id>/` | Interview report |
| `/admin/` | Django admin panel |

## 🗄️ Database Models

### Profile

Stores candidate details such as phone number, headline, preferred location, summary, skills, GitHub details, profile photo, and resume.

### Job

Stores job information including title, company, location, category, job type, salary, role details, education, skills required, company website, company logo, views, and website clicks.

### Application

Stores candidate applications, uploaded resume, skills, status, interview schedule, AI match scores, interview scores, salary suggestion, generated questions, submitted answers, and offer letter.

### SavedJob

Stores jobs saved by candidates for later viewing.

### ApplicationTimeline

Stores application status changes and HR/candidate activity history.

## 🧠 AI Matching Workflow

1. Candidate uploads or updates resume.
2. System extracts text from PDF or DOCX resume.
3. Job skills and resume content are compared.
4. TF-IDF and cosine similarity calculate semantic match.
5. Profile completion score is included in the final match percentage.
6. Jobs are ranked and recommended to the candidate.
7. During application review, interview and resume scores contribute to the final candidate score.

## 🔮 Future Enhancements

- Add REST API using Django REST Framework
- Add PostgreSQL support for production
- Add email SMTP configuration for real notifications
- Add advanced NLP resume parsing
- Add recruiter/company-specific accounts
- Add charts and analytics for HR dashboard
- Add deployment configuration for Render, Railway, or AWS

## 👨‍💻 Author

**Umesh Mahajan**

## 📜 License

This project is created for academic and learning purposes. You may update this section with your preferred license before publishing.

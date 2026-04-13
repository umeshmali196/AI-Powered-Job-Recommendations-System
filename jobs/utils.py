import re
import zipfile
from pathlib import Path
from random import Random

import PyPDF2
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


QUESTION_TEMPLATES = [
    "Tell us about a project where you used {skill} to solve a real problem.",
    "How would you approach a {role} task that depends heavily on {skill}?",
    "What trade-offs do you consider when working with {skill} in production?",
    "Describe a challenge you faced while learning or applying {skill}.",
    "How do you measure quality and success in work related to {skill}?",
    "What would be your first 30-day plan as a {role} joining this team?",
    "How do your strengths align with this {role} opportunity?",
    "Explain one improvement you would make to a recent project involving {skill}.",
    "How do you stay current with best practices for {skill} and related tools?",
    "What makes you a strong fit for this {role} at this stage of your career?",
]


def split_skills(raw_text):
    if not raw_text:
        return []
    return [skill.strip() for skill in re.split(r"[,/\n]", raw_text) if skill.strip()]


def normalize_words(text):
    return re.findall(r"[a-zA-Z0-9+#.]+", (text or "").lower())


def extract_text_from_pdf(pdf_file):
    text = ""
    try:
        with open(pdf_file, "rb") as file_handle:
            reader = PyPDF2.PdfReader(file_handle)
            for page in reader.pages:
                page_text = page.extract_text() or ""
                text += f" {page_text}"
    except Exception:
        return ""
    return text.strip()


def extract_text_from_docx(docx_file):
    try:
        with zipfile.ZipFile(docx_file) as archive:
            xml_content = archive.read("word/document.xml").decode("utf-8", errors="ignore")
    except Exception:
        return ""
    return re.sub(r"<[^>]+>", " ", xml_content)


def extract_text_from_resume(file_path):
    if not file_path:
        return ""

    suffix = Path(file_path).suffix.lower()
    if suffix == ".pdf":
        return extract_text_from_pdf(file_path)
    if suffix == ".docx":
        return extract_text_from_docx(file_path)
    return ""


def calculate_semantic_match(resume_text, job_text):
    documents = [(resume_text or "").strip(), (job_text or "").strip()]
    if not any(documents):
        return 0
    try:
        vectorizer = TfidfVectorizer(stop_words="english")
        tfidf_matrix = vectorizer.fit_transform(documents)
        similarity = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:2])[0][0]
    except ValueError:
        return 0
    return round(similarity * 100, 2)


def calculate_profile_completion(user, profile):
    completed_weight = 0
    total_weight = 0

    checks = [
        {"key": "name", "label": "Complete your name", "weight": 10, "done": bool(user.first_name.strip() and user.last_name.strip())},
        {"key": "email", "label": "Add email", "weight": 10, "done": bool((user.email or "").strip())},
        {"key": "phone_number", "label": "Add phone number", "weight": 10, "done": bool((profile.phone_number or "").strip())},
        {"key": "profile_photo", "label": "Add profile photo", "weight": 10, "done": bool(profile.profile_photo or profile.github_avatar_url)},
        {"key": "headline", "label": "Set professional headline", "weight": 10, "done": bool((profile.headline or "").strip())},
        {"key": "preferred_location", "label": "Add preferred location", "weight": 10, "done": bool((profile.preferred_location or "").strip())},
        {"key": "skills", "label": "Add key skills", "weight": 12, "done": bool((profile.skills or "").strip())},
        {"key": "summary", "label": "Write profile summary", "weight": 10, "done": bool((profile.summary or "").strip())},
        {"key": "resume", "label": "Upload resume", "weight": 13, "done": bool(profile.resume)},
        {"key": "github_username", "label": "Link GitHub", "weight": 5, "done": bool((profile.github_username or "").strip())},
    ]

    for check in checks:
        total_weight += check["weight"]
        if check["done"]:
            completed_weight += check["weight"]

    return round((completed_weight / total_weight) * 100, 2) if total_weight else 0


def get_profile_completion_checks(user, profile):
    return [
        {"key": "resume", "label": "Upload resume", "weight": 13, "done": bool(profile.resume)},
        {"key": "skills", "label": "Add key skills", "weight": 12, "done": bool((profile.skills or "").strip())},
        {"key": "summary", "label": "Write profile summary", "weight": 10, "done": bool((profile.summary or "").strip())},
        {"key": "headline", "label": "Set professional headline", "weight": 10, "done": bool((profile.headline or "").strip())},
        {"key": "preferred_location", "label": "Add preferred location", "weight": 10, "done": bool((profile.preferred_location or "").strip())},
        {"key": "phone_number", "label": "Add phone number", "weight": 10, "done": bool((profile.phone_number or "").strip())},
        {"key": "email", "label": "Verify email details", "weight": 10, "done": bool((user.email or "").strip())},
        {"key": "name", "label": "Complete your name", "weight": 10, "done": bool(user.first_name.strip() and user.last_name.strip())},
        {"key": "profile_photo", "label": "Add profile photo", "weight": 10, "done": bool(profile.profile_photo or profile.github_avatar_url)},
        {"key": "github_username", "label": "Link GitHub", "weight": 5, "done": bool((profile.github_username or "").strip())},
    ]


def calculate_resume_insights(user, profile, job, resume_text):
    resume_text = resume_text or ""
    resume_words = set(normalize_words(resume_text))
    job_skills = split_skills(job.skills_required)
    job_skill_words = [skill.lower() for skill in job_skills]
    matched_skills = [skill for skill in job_skills if skill.lower() in resume_text.lower()]
    missing_skills = [skill for skill in job_skills if skill.lower() not in resume_text.lower()]

    skill_match = (len(matched_skills) / len(job_skills) * 100) if job_skills else 0
    semantic_score = calculate_semantic_match(
        resume_text,
        " ".join(
            filter(
                None,
                [
                    job.title,
                    job.role,
                    job.description,
                    job.skills_required,
                    job.education,
                ],
            )
        ),
    )
    profile_completion = calculate_profile_completion(user, profile)

    resume_signal = 40
    resume_signal += min(len(resume_words), 300) / 6
    resume_signal += 10 if profile.summary else 0
    resume_signal += 8 if profile.github_username else 0
    resume_signal += min(len(split_skills(profile.skills or "")) * 4, 20)
    resume_score = round(min(resume_signal, 100), 2)

    match_percentage = round(
        (skill_match * 0.5) + (semantic_score * 0.35) + (profile_completion * 0.15),
        2,
    )
    missing_skill_count = len(missing_skills)

    if match_percentage >= 80:
        summary = "Strong role fit with solid skill overlap and a recruiter-ready profile."
    elif match_percentage >= 60:
        summary = "Promising fit with a few skill gaps that can be addressed before interview."
    else:
        summary = "Early-stage match. Filling the missing skills should improve alignment."

    return {
        "resume_score": resume_score,
        "semantic_score": semantic_score,
        "match_percentage": match_percentage,
        "matched_skills": matched_skills,
        "missing_skills": missing_skills,
        "missing_skill_count": missing_skill_count,
        "profile_completion": profile_completion,
        "summary": summary,
    }


def recommend_jobs_for_profile(user, profile, jobs, limit=6):
    resume_text = ""
    if profile.resume:
        resume_text = extract_text_from_resume(profile.resume.path)

    scored_jobs = []
    for job in jobs:
        insights = calculate_resume_insights(user, profile, job, resume_text)
        job.match_percentage = insights["match_percentage"]
        job.resume_score = insights["resume_score"]
        job.missing_skills = insights["missing_skills"]
        scored_jobs.append(job)

    scored_jobs.sort(key=lambda job: getattr(job, "match_percentage", 0), reverse=True)
    return scored_jobs[:limit]


def generate_interview_questions(application, count=8):
    job_skills = split_skills(application.job.skills_required)
    candidate_skills = split_skills(application.skills or application.matched_skills or "")
    skill_pool = candidate_skills or job_skills or [application.job.title]
    randomizer = Random(f"{application.id}-{application.user_id}-{application.job_id}")

    questions = []
    for index in range(count):
        skill = randomizer.choice(skill_pool)
        template = randomizer.choice(QUESTION_TEMPLATES)
        questions.append(
            {
                "id": index + 1,
                "skill": skill,
                "question": template.format(skill=skill, role=application.job.title),
                "keywords": list(
                    dict.fromkeys(
                        normalize_words(
                            f"{skill} {application.job.title} {application.job.skills_required}"
                        )
                    )
                )[:8],
            }
        )
    return questions


def evaluate_interview(application, answers):
    questions = application.generated_questions or generate_interview_questions(application)
    scored_answers = []
    technical_points = 0
    communication_points = 0
    confidence_points = 0

    for question, answer in zip(questions, answers):
        answer = (answer or "").strip()
        answer_words = normalize_words(answer)
        keyword_hits = len(set(answer_words) & set(question.get("keywords", [])))
        keyword_score = min(100, keyword_hits * 18)
        length_score = min(100, len(answer_words) * 3)
        assertive_terms = {"built", "led", "improved", "delivered", "optimized", "designed", "implemented"}
        confidence_hits = len(set(answer_words) & assertive_terms)
        confidence_score = min(100, 35 + (confidence_hits * 12) + min(len(answer_words), 60) * 0.6)
        communication_score = min(100, 30 + (len(answer.split(".")) * 8) + min(len(answer_words), 70) * 0.7)
        technical_score = round((keyword_score * 0.65) + (length_score * 0.35), 2)

        technical_points += technical_score
        communication_points += communication_score
        confidence_points += confidence_score
        scored_answers.append(
            {
                "question": question["question"],
                "answer": answer,
                "technical_score": round(technical_score, 2),
                "communication_score": round(min(communication_score, 100), 2),
                "confidence_score": round(min(confidence_score, 100), 2),
            }
        )

    total_answers = max(len(scored_answers), 1)
    technical_score = round(technical_points / total_answers, 2)
    communication_score = round(min(communication_points / total_answers, 100), 2)
    confidence_score = round(min(confidence_points / total_answers, 100), 2)
    overall_score = round(
        (technical_score * 0.45) + (communication_score * 0.3) + (confidence_score * 0.25),
        2,
    )

    if overall_score >= 80:
        summary = "Candidate communicated clearly and showed strong role-specific understanding."
    elif overall_score >= 65:
        summary = "Candidate showed good potential with room to deepen technical clarity."
    else:
        summary = "Candidate needs stronger technical depth and more structured communication."

    return {
        "answers": scored_answers,
        "technical_score": technical_score,
        "communication_score": communication_score,
        "confidence_score": confidence_score,
        "overall_score": overall_score,
        "summary": summary,
    }


def calculate_final_score(application):
    return round(
        (application.resume_score * 0.3)
        + (application.match_percentage * 0.25)
        + (application.interview_score * 0.45),
        2,
    )


def suggest_salary(application):
    numbers = [float(num) for num in re.findall(r"\d+(?:\.\d+)?", application.job.salary or "")]
    multiplier = 0.9 + (application.final_score / 100) * 0.25

    if len(numbers) >= 2:
        low = round(numbers[0] * multiplier, 1)
        high = round(numbers[1] * multiplier, 1)
        return f"AI suggested offer: {low} - {high} LPA"

    matched_skill_count = len(split_skills(application.matched_skills))
    base = max(4.5, 5 + matched_skill_count * 0.55)
    low = round(base + (application.final_score * 0.03), 1)
    high = round(low + 2.5, 1)
    return f"AI suggested offer: {low} - {high} LPA"


def build_offer_letter(application):
    return (
        f"Offer Letter\n\n"
        f"Candidate: {application.full_name}\n"
        f"Role: {application.job.title}\n"
        f"Company: {application.job.company}\n"
        f"Final Score: {application.final_score}%\n"
        f"Suggested Compensation: {application.salary_suggestion}\n\n"
        f"We are pleased to offer you the position of {application.job.title}. "
        f"Please connect with the HR team to complete onboarding formalities."
    )

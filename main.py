import os
import json
from typing import List, Optional
from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel
from pypdf import PdfReader
import docx


# =====================================
# Load Environment Variables & Client
# =====================================

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY not found in environment variables!")

client = Groq(api_key=api_key)

MODEL = "llama-3.3-70b-versatile"


# =====================================
# Helper Function: Text Extraction
# =====================================

def _extract_text(uploaded_file) -> str:
    """Extracts text safely from PDF or DOCX file."""
    uploaded_file.seek(0)
    filename = getattr(uploaded_file, "name", "").lower()

    if filename.endswith(".docx"):
        doc = docx.Document(uploaded_file)
        text = [p.text for p in doc.paragraphs if p.text.strip()]
        return "\n".join(text)
    else:
        reader = PdfReader(uploaded_file)
        text_parts = []
        for page in reader.pages:
            extracted = page.extract_text()
            if extracted:
                text_parts.append(extracted)
        return "\n".join(text_parts)


# =====================================
# Pydantic Schemas
# =====================================

class ResumeMatch(BaseModel):
    name: str
    email: str
    ats_score: int
    match_percentage: int
    matching_skills: List[str]
    missing_skills: List[str]
    strengths: List[str]
    weaknesses: List[str]
    suggestions: List[str]
    summary: str


class ContactInfo(BaseModel):
    email: str = ""
    phone: str = ""
    location: str = ""
    linkedin: str = ""
    portfolio: str = ""


class SkillCategory(BaseModel):
    category: str
    skills: List[str]


class ExperienceItem(BaseModel):
    title: str
    company: str
    location: str = ""
    dates: str = ""
    bullets: List[str]


class ProjectItem(BaseModel):
    name: str
    technologies: str = ""
    bullets: List[str]


class EducationItem(BaseModel):
    degree: str
    institution: str
    dates: str = ""
    location: str = ""


class ImprovedResume(BaseModel):
    name: str
    contact: ContactInfo
    summary: str
    skills: List[SkillCategory]
    experience: List[ExperienceItem]
    projects: List[ProjectItem]
    education: List[EducationItem]
    certifications: List[str]


# =====================================
# Main Analysis Function
# =====================================

def analyze_resume(uploaded_file, job_description: str) -> dict:
    """Analyzes resume against Job Description using Groq & Pydantic Schema."""
    resume_text = _extract_text(uploaded_file)
    schema = ResumeMatch.model_json_schema()

    system_prompt = f"""
You are an ATS Resume Analyzer.
Compare the Resume with the Job Description.
Return ONLY JSON according to this schema:
{json.dumps(schema)}

Rules:
1. ATS Score between 0-100
2. Match Percentage between 0-100
3. Compare Resume with Job Description.
4. Extract matching skills.
5. Extract missing skills.
6. Mention strengths.
7. Mention weaknesses.
8. Give professional suggestions.
9. Provide a concise 2-3 sentence overall summary of candidate fit.

Return JSON only.
"""

    user_prompt = f"""
Resume:
{resume_text}

===================================

Job Description:
{job_description}
"""

    response = client.chat.completions.create(
        model=MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    data = json.loads(response.choices[0].message.content)
    analysis = ResumeMatch(**data)
    return analysis.model_dump()


# =====================================
# Improved Resume Rewriter Function
# =====================================

def generate_improved_resume(uploaded_file, job_description: str) -> dict:
    """Rewrites and optimizes candidate's resume for JD using Groq LLM."""
    resume_text = _extract_text(uploaded_file)
    schema = ImprovedResume.model_json_schema()

    system_prompt = f"""
You are an Executive Resume Writer & ATS Optimization Specialist.
Your task is to rewrite the candidate's resume to optimize it for the Job Description.

STRICT RULES:
1. NEVER invent fake experience, degrees, or companies. Keep all factual candidate info truthful.
2. Add relevant missing keywords from the JD naturally into skills, summary, and experience.
3. Rewrite bullet points using strong action verbs and quantifiable metrics where possible.
4. Keep professional tone and structure into standard sections.
5. Return ONLY a JSON object strictly matching this schema:
{json.dumps(schema)}
"""

    user_prompt = f"""
Resume:
{resume_text}

===================================

Job Description:
{job_description}
"""

    response = client.chat.completions.create(
        model=MODEL,
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]
    )

    data = json.loads(response.choices[0].message.content)
    improved = ImprovedResume(**data)
    return improved.model_dump()
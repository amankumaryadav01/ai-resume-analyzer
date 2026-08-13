"""
models/optimized_resume.py

Schema for the AI-rewritten, JD-aligned resume. Nested entries
(ExperienceEntry, ProjectEntry, EducationEntry) are typed models rather
than plain dicts, per the original spec — this trades a small deviation
from the literal spec (`list[dict]`) for actual validation and reliable
field access in report_service.py's PDF layout code. Untyped dicts would
let a malformed LLM response silently produce a broken PDF instead of
failing loudly at the Pydantic validation step.
"""

from pydantic import BaseModel


class ExperienceEntry(BaseModel):
    title: str
    company: str = ""
    duration: str = ""
    bullets: list[str]


class ProjectEntry(BaseModel):
    name: str
    bullets: list[str]
    tech_stack: list[str] = []


class EducationEntry(BaseModel):
    degree: str
    institution: str = ""
    duration: str = ""


class OptimizedResume(BaseModel):
    target_role: str

    professional_summary: str

    technical_skills: dict[str, list[str]]

    experience: list[ExperienceEntry]

    projects: list[ProjectEntry]

    education: list[EducationEntry]

    certifications: list[str]

    achievements: list[str]

    keywords_added: list[str]
    keywords_matched: list[str]
    missing_keywords: list[str]

    optimization_notes: list[str]
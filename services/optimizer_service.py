import os
import json
import re
from groq import Groq

client = Groq(api_key=os.getenv("GROQ_API_KEY"))


# ---------------------------------------------------------
# Helpers
# ---------------------------------------------------------

def _normalize(text):
    return re.sub(r"[^a-z0-9]+", " ", str(text).lower()).strip()


def _dedupe_list(items):
    result = []
    seen = set()

    for item in items or []:
        if not item:
            continue

        value = str(item).strip()
        key = _normalize(value)

        if key and key not in seen:
            seen.add(key)
            result.append(value)

    return result


def _is_bullet_similar(b1, b2):
    """Calculates word-overlap similarity between two bullets."""
    w1 = set(_normalize(b1).split())
    w2 = set(_normalize(b2).split())
    if not w1 or not w2:
        return False
    intersection = w1 & w2
    min_len = min(len(w1), len(w2))
    if min_len == 0:
        return False
    return (len(intersection) / min_len) >= 0.55


def _merge_skill_categories(original, optimized):
    """
    Preserve ALL skills already present in the original resume.
    AI can reorganize/reword them but cannot remove them.
    """
    optimized = optimized or {}
    result = {}

    for category, skills in (optimized.get("technical_skills") or {}).items():
        result[category] = _dedupe_list(skills)

    skill_groups = {
        "Programming Languages": [
            "C++", "Java", "Python", "JavaScript",
        ],
        "Core CS Fundamentals": [
            "Data Structures & Algorithms", "Competitive Programming",
            "Object-Oriented Programming", "OOP", "OOPs",
            "Database Management Systems", "DBMS", "Operating Systems",
        ],
        "Data Analysis & Visualization": [
            "Pandas", "NumPy", "Matplotlib", "Seaborn", "Plotly",
        ],
        "Web Development": [
            "HTML", "CSS", "ReactJS", "React.js", "React",
            "MERN Stack", "MongoDB", "Express.js", "Node.js",
        ],
        "AI & Software Development": [
            "Prompt Engineering", "ChatGPT", "Gemini", "Claude",
            "Software Development Life Cycle", "SDLC", "Agile Methodologies",
            "Agile", "REST APIs", "REST API", "Basic Database Concepts",
            "Process Documentation", "User Stories", "Functional Specifications",
            "LLMs", "Large Language Models",
        ],
        "Tools & Version Control": [
            "Git", "GitHub",
        ],
    }

    original_lower = original.lower()

    for category, possible_skills in skill_groups.items():
        if category not in result:
            result[category] = []

        for skill in possible_skills:
            if skill.lower() in original_lower:
                existing_normalized = {
                    _normalize(x) for x in result[category]
                }
                if _normalize(skill) not in existing_normalized:
                    result[category].append(skill)

    return {
        category: _dedupe_list(skills)
        for category, skills in result.items()
        if skills
    }


def _remove_duplicate_projects(data):
    """
    A project must not appear in both Experience and Projects.
    If similar text/bullets appear in both, keep it ONLY under Projects.
    """
    projects = data.get("projects") or []
    experience = data.get("experience") or []

    project_signatures = set()
    project_bullets = []

    for p in projects:
        if not isinstance(p, dict):
            continue
        p_name = _normalize(p.get("name") or p.get("title") or "")
        if p_name:
            project_signatures.add(p_name)

        for b in p.get("bullets") or []:
            if b:
                project_bullets.append(str(b))

    cleaned_experience = []

    for exp in experience:
        if not isinstance(exp, dict):
            continue

        title = exp.get("title", "")
        company = exp.get("company", "")
        title_norm = _normalize(title)
        comp_norm = _normalize(company)
        exp_comb = _normalize(f"{title} {company}")

        is_duplicate = False

        # 1. Check if project name matches title or company
        for p_sig in project_signatures:
            if not p_sig:
                continue
            if (p_sig in title_norm or p_sig in comp_norm or p_sig in exp_comb or
                title_norm in p_sig or (comp_norm and comp_norm in p_sig)):
                is_duplicate = True
                break

        # 2. Check if experience bullets overlap significantly with project bullets
        if not is_duplicate:
            exp_bullets = exp.get("bullets") or []
            similar_count = 0
            for eb in exp_bullets:
                for pb in project_bullets:
                    if _is_bullet_similar(eb, pb):
                        similar_count += 1
                        break

            if len(exp_bullets) > 0 and (similar_count / len(exp_bullets)) >= 0.3:
                is_duplicate = True

        if not is_duplicate:
            cleaned_experience.append(exp)

    data["experience"] = cleaned_experience
    return data


# ---------------------------------------------------------
# Main optimizer
# ---------------------------------------------------------

def generate_optimized_resume(
    resume_text,
    job_description,
    analysis_result,
):
    prompt = f"""
You are an expert ATS resume optimizer.

You MUST optimize the resume using ONLY information present in the ORIGINAL RESUME.

==========================================================
ORIGINAL RESUME
==========================================================
{resume_text}

==========================================================
JOB DESCRIPTION
==========================================================
{job_description}

==========================================================
EXISTING ATS ANALYSIS
==========================================================
{json.dumps(analysis_result or {}, indent=2)}

==========================================================
STRICT RULES
==========================================================

1. ORIGINAL INFORMATION MUST BE PRESERVED
Do NOT delete valid information from the original resume.
Preserve: name, email, phone, location, professional_summary, ALL technical_skills, education, certifications, projects, genuine employment/internship experience.

2. EXPERIENCE VS PROJECTS (CRITICAL)
- 'experience' is STRICTLY for formal employment, internships, or job roles at companies/organizations.
- Academic projects, personal projects, hackathons, and self-built applications MUST go under 'projects' ONLY.
- DO NOT convert projects into experience entries or invent generic titles like 'Developer' or 'Full-Stack Developer' for projects.
- Do NOT list the same project in both 'experience' and 'projects'.
- If the candidate has no formal job or internship experience at a company, return "experience": [].

3. TECHNICAL SKILLS
Every legitimate skill in the original resume MUST remain in technical_skills organized by categories (e.g., Programming Languages, Core CS Fundamentals, Data Analysis & Visualization, Web Development, AI & Software Development, Tools & Version Control).

4. PROFESSIONAL SUMMARY
Write a strong professional summary accurately reflecting the candidate's skills and target role.

5. NEVER INVENT
Never invent companies, titles, skills, or experience not present in the original resume.

==========================================================
RETURN ONLY VALID JSON
==========================================================
{{
    "name": "",
    "email": "",
    "phone": "",
    "location": "",
    "professional_summary": "",
    "technical_skills": {{
        "Programming Languages": [],
        "Core CS Fundamentals": [],
        "Data Analysis & Visualization": [],
        "Web Development": [],
        "AI & Software Development": [],
        "Tools & Version Control": []
    }},
    "experience": [],
    "projects": [
        {{
            "name": "",
            "duration": "",
            "technologies": "",
            "bullets": []
        }}
    ],
    "education": [
        {{
            "degree": "",
            "institution": "",
            "dates": ""
        }}
    ],
    "certifications": [],
    "keywords_matched": [],
    "keywords_added": [],
    "missing_keywords": [],
    "optimization_notes": [],
    "target_role": ""
}}

Return complete JSON only.
"""

    response = client.chat.completions.create(
       model="openai/gpt-oss-120b",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a strict ATS resume optimizer. "
                    "Never hallucinate information. "
                    "Never remove valid original resume information."
                ),
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0.1,
    )

    content = response.choices[0].message.content.strip()

    if content.startswith("```"):
        content = re.sub(r"^```(?:json)?", "", content, flags=re.IGNORECASE)
        content = re.sub(r"```$", "", content).strip()

    optimized = json.loads(content)

    # Protection layer
    optimized["technical_skills"] = _merge_skill_categories(
        resume_text,
        optimized.get("technical_skills") or {},
    )

    optimized["certifications"] = _dedupe_list(
        optimized.get("certifications") or []
    )

    optimized = _remove_duplicate_projects(optimized)

    optimized["keywords_matched"] = _dedupe_list(optimized.get("keywords_matched"))
    optimized["keywords_added"] = _dedupe_list(optimized.get("keywords_added"))
    optimized["missing_keywords"] = _dedupe_list(optimized.get("missing_keywords"))
    optimized["optimization_notes"] = _dedupe_list(optimized.get("optimization_notes"))

    return optimized
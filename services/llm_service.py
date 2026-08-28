import os
import json
from typing import List

from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel
from pypdf import PdfReader
import docx


# ============================================================
# ENVIRONMENT + GROQ CLIENT
# ============================================================

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY not found in environment variables!")

client = Groq(api_key=api_key)

MODEL = "openai/gpt-oss-120b"


# ============================================================
# PDF / DOCX TEXT EXTRACTION
# ============================================================

def extract_resume_text(uploaded_file) -> str:
    """
    Extract text safely from PDF or DOCX resume.
    """

    uploaded_file.seek(0)

    filename = getattr(uploaded_file, "name", "").lower()

    if filename.endswith(".docx"):
        document = docx.Document(uploaded_file)

        text = [
            paragraph.text
            for paragraph in document.paragraphs
            if paragraph.text.strip()
        ]

        return "\n".join(text)

    elif filename.endswith(".pdf"):
        reader = PdfReader(uploaded_file)

        text_parts = []

        for page in reader.pages:
            extracted = page.extract_text()

            if extracted:
                text_parts.append(extracted)

        return "\n".join(text_parts)

    else:
        raise ValueError("Unsupported file format. Please upload PDF or DOCX.")


# ============================================================
# PYDANTIC SCHEMA
# ============================================================

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


# ============================================================
# ATS RESUME ANALYSIS
# ============================================================

def analyze_resume(uploaded_file, job_description: str) -> dict:
    """
    Analyze uploaded resume against the provided job description.

    Returns:
        dict containing ATS score, match percentage,
        matching skills, missing skills, strengths,
        weaknesses, suggestions and summary.
    """

    # --------------------------------------------------------
    # Extract resume text
    # --------------------------------------------------------

    resume_text = extract_resume_text(uploaded_file)

    if not resume_text.strip():
        raise ValueError(
            "Could not extract text from the uploaded resume."
        )

    if not job_description.strip():
        raise ValueError(
            "Job description cannot be empty."
        )

    # --------------------------------------------------------
    # Pydantic JSON schema
    # --------------------------------------------------------

    schema = ResumeMatch.model_json_schema()

    # --------------------------------------------------------
    # System prompt
    # --------------------------------------------------------

    system_prompt = f"""
You are an expert ATS Resume Analyzer and Senior Technical Recruiter.

Your job is to compare a candidate's resume against a job description.

Return ONLY a valid JSON object matching this schema:

{json.dumps(schema, indent=2)}

STRICT SCORING RULES:

1. ATS score must be an integer between 0 and 100.

2. Match percentage must be an integer between 0 and 100.

3. Do NOT give an unnecessarily high score.

4. A resume should receive:
   - 90-100 only when it is an excellent match.
   - 80-89 when it is a strong match.
   - 70-79 when it is a reasonably good match.
   - 60-69 when it has several important gaps.
   - 40-59 when it has major gaps.
   - Below 40 when the resume is poorly aligned.

5. Compare the actual resume against the actual job description.

6. matching_skills:
   Include skills that are clearly present in both the resume
   and relevant job requirements.

7. missing_skills:
   Include important job requirements that are missing
   from the resume.

8. strengths:
   Mention genuine strengths based only on the resume.

9. weaknesses:
   Mention genuine gaps or weaknesses relative to the job description.

10. suggestions:
    Give practical and professional suggestions for improving
    the resume.

11. summary:
    Provide a concise 2-3 sentence explanation of the candidate's
    overall fit.

12. NEVER invent candidate information.

13. NEVER invent skills, companies, education, experience,
    certifications, metrics or achievements.

14. Return JSON only.
"""

    # --------------------------------------------------------
    # User prompt
    # --------------------------------------------------------

    user_prompt = f"""
RESUME:
-------------------------
{resume_text}

-------------------------

JOB DESCRIPTION:
-------------------------
{job_description}

-------------------------

Analyze the resume against the job description now.
"""

    # --------------------------------------------------------
    # Groq API call
    # --------------------------------------------------------

    try:

        response = client.chat.completions.create(
            model=MODEL,
            response_format={"type": "json_object"},
            messages=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt
                }
            ],
            temperature=0.1
        )

    except Exception as e:

        raise RuntimeError(
            f"Groq API error: {str(e)}"
        ) from e

    # --------------------------------------------------------
    # Parse JSON
    # --------------------------------------------------------

    try:

        content = response.choices[0].message.content

        data = json.loads(content)

    except Exception as e:

        raise RuntimeError(
            f"Failed to parse Groq response as JSON: {str(e)}"
        ) from e

    # --------------------------------------------------------
    # Validate using Pydantic
    # --------------------------------------------------------

    try:

        analysis = ResumeMatch(**data)

    except Exception as e:

        raise RuntimeError(
            f"Invalid ATS analysis response: {str(e)}"
        ) from e

    # --------------------------------------------------------
    # Return dictionary
    # --------------------------------------------------------

    return analysis.model_dump()
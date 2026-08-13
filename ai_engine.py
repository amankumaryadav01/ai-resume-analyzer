import json
import google.generativeai as genai

def setup_gemini_client(api_key: str):
    """Configure Gemini API key."""
    if not api_key or not api_key.strip():
        raise ValueError("Google Gemini API Key is missing. Please provide a valid key.")
    genai.configure(api_key=api_key.strip())

def analyze_ats(resume_text: str, job_description: str, api_key: str) -> dict:
    """
    Analyzes the resume against the job description using Gemini.
    Returns structured ATS evaluation data.
    """
    setup_gemini_client(api_key)

    prompt = f"""
You are an expert ATS (Applicant Tracking System) optimization consultant and Senior Tech Recruiter.
Analyze the following resume against the job description.

Job Description:
{job_description}

Resume:
{resume_text}

Provide your analysis in clean JSON format matching this exact schema:
{{
    "ats_score": 85,
    "matching_skills": ["Skill 1", "Skill 2"],
    "missing_skills": ["Skill 3", "Skill 4"],
    "strengths": ["Strength 1", "Strength 2"],
    "weaknesses": ["Weakness 1", "Weakness 2"],
    "suggestions": ["Suggestion 1", "Suggestion 2"]
}}
"""

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text)
    except Exception as e:
        raise RuntimeError(f"Error during ATS analysis: {str(e)}")

def generate_improved_resume(resume_text: str, job_description: str, api_key: str) -> dict:
    """
    Rewrites and optimizes the resume using Gemini while retaining truthfulness.
    Returns structured JSON data to build PDF/DOCX reliably.
    """
    setup_gemini_client(api_key)

    prompt = f"""
You are an expert Executive Resume Writer and ATS Optimization Specialist.
Your task is to rewrite the candidate's resume to optimize it for the provided Job Description.

STRICT REWRITE RULES:
1. NEVER invent fake experience, degrees, or companies. Keep all truthful candidate information intact.
2. Incorporate relevant missing keywords and skills naturally from the Job Description into experience and skills sections.
3. Rewrite experience bullet points using strong action verbs, quantifiable achievements, and concise phrasing.
4. Enhance the Professional Summary to align with the targeted role.
5. Order the final document strictly into these 8 sections:
   1. Name
   2. Contact
   3. Professional Summary
   4. Skills
   5. Experience
   6. Projects
   7. Education
   8. Certifications

Return ONLY a single valid JSON object following this exact schema:
{{
    "name": "Full Name",
    "contact": {{
        "email": "email@example.com",
        "phone": "+1234567890",
        "location": "City, State/Country",
        "linkedin": "linkedin.com/in/username",
        "portfolio": "github.com/username or portfolio link"
    }},
    "summary": "Compelling 3-4 sentence professional summary tailored to job keywords...",
    "skills": [
        {{"category": "Technical Skills", "skills": ["Python", "Streamlit", "SQL"]}},
        {{"category": "Tools & Frameworks", "skills": ["Git", "Docker", "AWS"]}},
        {{"category": "Soft Skills", "skills": ["Problem Solving", "Leadership"]}}
    ],
    "experience": [
        {{
            "title": "Job Title",
            "company": "Company Name",
            "location": "City, Country",
            "dates": "Month Year - Month Year or Present",
            "bullets": [
                "Action verb + task + quantifiable metric/result incorporating target keywords.",
                "Another strong achievement bullet point."
            ]
        }}
    ],
    "projects": [
        {{
            "name": "Project Name",
            "technologies": "Python, Streamlit, Gemini API",
            "bullets": [
                "Key achievement or implementation detail.",
                "Impact or result of the project."
            ]
        }}
    ],
    "education": [
        {{
            "degree": "Degree Title",
            "institution": "University / School Name",
            "dates": "Graduation Year or Date Range",
            "location": "City, Country"
        }}
    ],
    "certifications": [
        "Certification Name 1 - Issuer (Year)",
        "Certification Name 2 - Issuer (Year)"
    ]
}}

Job Description:
{job_description}

Original Resume:
{resume_text}
"""

    try:
        model = genai.GenerativeModel("gemini-1.5-flash")
        response = model.generate_content(
            prompt,
            generation_config={"response_mime_type": "application/json"}
        )
        return json.loads(response.text)
    except Exception as e:
        raise RuntimeError(f"Error generating improved resume: {str(e)}")
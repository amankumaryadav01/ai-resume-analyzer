import os
import json
from dotenv import load_dotenv
from groq import Groq
from pydantic import BaseModel
from pypdf import PdfReader


# =====================================
# Load Environment Variables
# =====================================

load_dotenv()

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise ValueError("GROQ_API_KEY not found!")

client = Groq(api_key=api_key)

MODEL = "llama-3.3-70b-versatile"


# =====================================
# Pydantic Model
# =====================================

class ResumeMatch(BaseModel):

    name: str
    email: str

    ats_score: int
    match_percentage: int

    matching_skills: list[str]
    missing_skills: list[str]

    strengths: list[str]
    weaknesses: list[str]

    suggestions: list[str]


# =====================================
# Main Function For Streamlit
# =====================================

def analyze_resume(pdf_file, job_description):


    # Read Uploaded PDF

    reader = PdfReader(pdf_file)

    resume = ""

    for page in reader.pages:

        text = page.extract_text()

        if text:
            resume += text + "\n"


    schema = ResumeMatch.model_json_schema()


    # =====================================
    # System Prompt
    # =====================================

    system_prompt = f"""
You are an ATS Resume Analyzer.

Compare the Resume with the Job Description.

Return ONLY JSON according to this schema.

{schema}

Rules:

1. ATS Score between 0-100

2. Match Percentage between 0-100

3. Compare Resume with Job Description.

4. Extract matching skills.

5. Extract missing skills.

6. Mention strengths.

7. Mention weaknesses.

8. Give professional suggestions.

Return JSON only.
"""


    user_prompt = f"""

Resume:

{resume}


===================================


Job Description:

{job_description}

"""


    # =====================================
    # Groq API Call
    # =====================================

    response = client.chat.completions.create(

        model=MODEL,

        response_format={
            "type":"json_object"
        },

        messages=[

            {
                "role":"system",
                "content":system_prompt
            },

            {
                "role":"user",
                "content":user_prompt
            }

        ]
    )


    answer = response.choices[0].message.content


    # JSON Convert

    data = json.loads(answer)


    analysis = ResumeMatch(**data)


    return analysis.model_dump()
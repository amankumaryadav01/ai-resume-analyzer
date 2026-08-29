AI Resume Analyzer

An AI-powered ATS Resume Analyzer built with Streamlit, Groq LLM, Pydantic, and Python. Upload a resume, paste a job description, and get an ATS-focused analysis with skill gaps, strengths, weaknesses, suggestions, and an AI-generated summary.

🚀 Live Demo

Live App: https://ai-resume-analyzer-csvcksqfnpjnp4gybnsaae.streamlit.app/

✨ Features

📄 Upload a resume in PDF format

🎯 Paste a complete job description

🤖 AI-powered ATS resume analysis

📊 ATS score and match percentage

✅ Matching skills identification

⚠️ Missing skills / skill-gap analysis

💪 Resume strengths

🔍 Resume weaknesses

💡 Actionable improvement suggestions

📝 Concise AI-generated candidate-fit summary

🚀 Generate an optimized resume aligned with the job description

🛡️ Optimization rules designed to preserve original resume information and avoid inventing skills, employers, experience, metrics, or achievements

📑 Export ATS diagnostic reports as PDF/DOCX

📄 Generate optimized resume documents as PDF/DOCX

🌙 Light/Dark theme support in the Streamlit interface

🧠 How It Works

Resume (PDF)
     │
     ▼
Text Extraction
     │
     ▼
Job Description + Resume
     │
     ▼
Groq LLM
     │
     ▼
Structured ATS Analysis
     │
     ├── ATS Score
     ├── Match Percentage
     ├── Matching Skills
     ├── Missing Skills
     ├── Strengths
     ├── Weaknesses
     ├── Suggestions
     └── Summary
     │
     ▼
Optional Resume Optimization
     │
     ▼
PDF / DOCX Export

🛠️ Tech Stack

Technology

Purpose

Python

Application development

Streamlit

Web application UI

Groq

LLM inference

openai/gpt-oss-120b

AI model used for analysis/optimization

Pydantic

Structured response validation

pypdf

PDF text extraction

python-docx

DOCX reading and document generation

ReportLab

PDF report generation

Plotly

Charts and visualizations

Pandas

Data handling

python-dotenv

Local environment variable loading

📁 Project Structure

AI-Resume-Analyzer/
│
├── .streamlit/
│   └── secrets.toml          # Local secrets (ignored by Git)
│
├── config/
│   ├── __init__.py
│   └── settings.py
│
├── database/
│   └── db.py
│
├── models/
│   ├── __init__.py
│   ├── optimized_resume.py
│   └── resume_analysis.py
│
├── services/
│   ├── __init__.py
│   ├── llm_service.py        # Groq + ATS analysis
│   ├── optimizer_service.py  # Resume optimization
│   ├── pdf_service.py        # Resume text extraction
│   └── report_service.py     # PDF/DOCX report generation
│
├── utils/
│   ├── __init__.py
│   └── error_handler.py
│
├── app.py                    # Streamlit application
├── ai_engine.py
├── database.py
├── main.py
├── report_generator.py
├── utils.py
├── requirements.txt
├── runtime.txt
├── .env.example
├── .gitignore
└── README.md

⚙️ Installation

1. Clone the repository

git clone https://github.com/amankumaryadav01/ai-resume-analyzer.git
cd ai-resume-analyzer

2. Create a virtual environment

Windows PowerShell:

python -m venv .venv
.\.venv\Scripts\Activate.ps1

3. Install dependencies

pip install -r requirements.txt

If your current requirements.txt is used for the full report-generation functionality, make sure python-docx is also included because the project imports docx.

4. Configure the Groq API key

For local development, create a .env file:

GROQ_API_KEY=your_groq_api_key

Never commit .env or real API keys to GitHub.

The application loads the key with python-dotenv.

▶️ Run Locally

streamlit run app.py

Then open the local Streamlit URL shown in the terminal.

☁️ Streamlit Cloud Deployment

For Streamlit Cloud:

Connect the GitHub repository.

Select the main branch.

Set the main file to:

app.py

Open Advanced settings → Secrets.

Add:

GROQ_API_KEY = "your_groq_api_key"

Deploy the application.

The .streamlit/secrets.toml file should remain local and must not contain production secrets in the Git repository.

🔐 Security

This project intentionally ignores sensitive local files such as:

.env
.streamlit/secrets.toml
.venv/
venv/
__pycache__/
*.pyc

If an API key has ever been exposed publicly, revoke/rotate that key and create a new one.

📊 ATS Analysis Output

The analyzer returns structured information including:

Candidate name and email

ATS score

Match percentage

Matching skills

Missing skills

Strengths

Weaknesses

Suggestions

Overall summary

The analysis uses explicit scoring guidance and validates the LLM response through a Pydantic schema.

🚀 Resume Optimization

The optimizer uses the original resume, job description, and ATS analysis to generate an optimized resume.

Important safeguards include:

Preserve valid original resume information

Preserve technical skills

Do not invent companies, titles, skills, experience, certifications, metrics, or achievements

Keep projects separate from formal employment/internship experience

Avoid duplicating projects as work experience

The generated optimized resume can be exported as PDF/DOCX.

📄 Reports

The project supports generation of:

ATS Diagnostic PDF

ATS Diagnostic DOCX

Optimized Resume PDF

Optimized Resume DOCX

The optimized document generation uses the same optimized data displayed by the application rather than performing a second AI generation.

🔮 Future Improvements

Possible future improvements:

DOCX upload directly from the main UI

Resume version history

Multiple job-description comparison

Resume keyword heatmap

More ATS scoring dimensions

User authentication

Persistent database-backed scan history

Additional LLM providers

More export templates

👨‍💻 Author

Aman Kumar Yadav

GitHub: https://github.com/amankumaryadav01

📜 License

Add your preferred open-source license here before publishing the project for external contributions.
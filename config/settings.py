import os

from dotenv import load_dotenv

load_dotenv()


# ============================================================
# API CONFIGURATION
# ============================================================

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

DATABASE_URL = os.getenv("DATABASE_URL")


# ============================================================
# LLM CONFIGURATION
# ============================================================

MODEL = "openai/gpt-oss-120b"


# ============================================================
# VALIDATION
# ============================================================

def get_groq_api_key() -> str:
    """Return Groq API key."""

    if not GROQ_API_KEY:
        raise RuntimeError(
            "GROQ_API_KEY not found. "
            "Add it to your .env file."
        )

    return GROQ_API_KEY


def get_database_url() -> str:
    """Return PostgreSQL database URL."""

    if not DATABASE_URL:
        raise RuntimeError(
            "DATABASE_URL not found. "
            "Add it to your .env file or Streamlit secrets."
        )

    return DATABASE_URL

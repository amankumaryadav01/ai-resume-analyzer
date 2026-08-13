"""
database.py

Persistence layer for scan history. Kept separate from app.py (UI) and
main.py (LLM analysis) per clean-architecture requirement — nothing here
imports streamlit, and nothing in app.py should write raw SQL directly.

Uses Postgres (e.g. Supabase) rather than local SQLite because Streamlit
Community Cloud's filesystem is ephemeral — a SQLite file would be wiped
on every app restart/redeploy, silently losing all history.
"""

import os
import json
from contextlib import contextmanager

import psycopg2
import psycopg2.extras


def _get_connection_string() -> str:
    """
    Reads the DB connection string from Streamlit secrets when running
    inside Streamlit, falling back to an environment variable otherwise
    (useful for local scripts/tests that don't have a Streamlit context).
    """
    try:
        import streamlit as st
        if "DATABASE_URL" in st.secrets:
            return st.secrets["DATABASE_URL"]
    except Exception:
        pass

    url = os.getenv("DATABASE_URL")
    if not url:
        raise RuntimeError(
            "DATABASE_URL not found. Set it in .streamlit/secrets.toml "
            "(local) or in Streamlit Cloud's Secrets settings (deployed)."
        )
    return url


@contextmanager
def get_connection():
    """Opens a short-lived connection per call rather than holding a
    persistent global connection — simpler to reason about across
    Streamlit's rerun-per-interaction model, at the cost of a small
    per-call connection overhead."""
    conn = psycopg2.connect(_get_connection_string())
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    """Creates the scans table if it doesn't already exist. Safe to call
    on every app startup."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS resume_scans (
                    id SERIAL PRIMARY KEY,
                    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
                    resume_filename TEXT,
                    job_title TEXT,
                    job_description TEXT,
                    resume_text TEXT,
                    ats_score INTEGER,
                    match_percentage INTEGER,
                    matching_skills JSONB,
                    missing_skills JSONB,
                    strengths JSONB,
                    weaknesses JSONB,
                    suggestions JSONB,
                    summary TEXT,
                    candidate_name TEXT,
                    candidate_email TEXT
                );
            """)
            cur.execute("""
                CREATE INDEX IF NOT EXISTS idx_resume_scans_created_at
                ON resume_scans (created_at DESC);
            """)


def add_scan(
    result: dict,
    resume_filename: str,
    job_title: str,
    job_description: str,
    resume_text: str,
) -> int:
    """Stores one completed analysis. Returns the new row's id."""
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO resume_scans (
                    resume_filename, job_title, job_description, resume_text,
                    ats_score, match_percentage,
                    matching_skills, missing_skills, strengths, weaknesses,
                    suggestions, summary, candidate_name, candidate_email
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING id;
            """, (
                resume_filename, job_title, job_description, resume_text,
                result.get("ats_score"), result.get("match_percentage"),
                json.dumps(result.get("matching_skills") or []),
                json.dumps(result.get("missing_skills") or []),
                json.dumps(result.get("strengths") or []),
                json.dumps(result.get("weaknesses") or []),
                json.dumps(result.get("suggestions") or []),
                result.get("summary"),
                result.get("name"),
                result.get("email"),
            ))
            return cur.fetchone()[0]


def _row_to_dict(row: dict) -> dict:
    """Un-jsonify the list columns coming back as JSONB."""
    for key in ("matching_skills", "missing_skills", "strengths", "weaknesses", "suggestions"):
        if row.get(key) is not None and isinstance(row[key], str):
            row[key] = json.loads(row[key])
    return dict(row)


def get_history(
    search: str = None,
    sort_by: str = "created_at",
    ascending: bool = False,
    limit: int = 20,
    offset: int = 0,
) -> list[dict]:
    """
    Returns a page of scan history, optionally filtered by a search term
    matched against resume filename and job title, and sorted by either
    date or ATS score.
    """
    if sort_by not in ("created_at", "ats_score", "match_percentage"):
        sort_by = "created_at"
    direction = "ASC" if ascending else "DESC"

    where_clause = ""
    params = []
    if search:
        where_clause = "WHERE resume_filename ILIKE %s OR job_title ILIKE %s"
        like = f"%{search}%"
        params.extend([like, like])

    query = f"""
        SELECT id, created_at, resume_filename, job_title, ats_score,
               match_percentage, matching_skills, missing_skills,
               candidate_name, candidate_email, summary
        FROM resume_scans
        {where_clause}
        ORDER BY {sort_by} {direction}
        LIMIT %s OFFSET %s;
    """
    params.extend([limit, offset])

    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute(query, params)
            rows = cur.fetchall()
            return [_row_to_dict(r) for r in rows]


def count_history(search: str = None) -> int:
    """Total matching rows — needed for pagination controls in the UI."""
    where_clause = ""
    params = []
    if search:
        where_clause = "WHERE resume_filename ILIKE %s OR job_title ILIKE %s"
        like = f"%{search}%"
        params.extend([like, like])

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(f"SELECT COUNT(*) FROM resume_scans {where_clause};", params)
            return cur.fetchone()[0]


def get_scan_by_id(scan_id: int) -> dict | None:
    """Full record, including resume_text and job_description — used for
    re-opening a past report or for version comparison."""
    with get_connection() as conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute("SELECT * FROM resume_scans WHERE id = %s;", (scan_id,))
            row = cur.fetchone()
            return _row_to_dict(row) if row else None


def delete_scan(scan_id: int) -> bool:
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM resume_scans WHERE id = %s;", (scan_id,))
            return cur.rowcount >
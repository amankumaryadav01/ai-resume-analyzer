import html
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from services.llm_service import analyze_resume
from services.report_service import generate_pdf_bytes, generate_docx_bytes, generate_optimized_resume_pdf
from services.pdf_service import extract_resume_text
from services.optimizer_service import generate_optimized_resume
from utils.error_handler import safe_error_message


# =====================================================================
# PAGE CONFIG
# =====================================================================

st.set_page_config(
    page_title="AI Resume Analyzer",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# =====================================================================
# THEME STATE
# =====================================================================

if "theme" not in st.session_state:
    st.session_state.theme = "light"


def get_palette(theme: str) -> dict:
    if theme == "dark":
        return {
            "bg": "#0B0D12", "surface": "#14171F", "border": "#262A35",
            "text": "#F3F4F6", "text_muted": "#9AA0AC",
            "primary": "#818CF8", "primary_soft": "rgba(129,140,248,0.15)",
            "green": "#34D399", "green_soft": "rgba(52,211,153,0.14)",
            "amber": "#FBBF24", "amber_soft": "rgba(251,191,36,0.14)",
            "red": "#F87171", "red_soft": "rgba(248,113,113,0.14)",
            "on_accent": "#0B0D12",
            "shadow": "0 0 0 1px rgba(255,255,255,0.04)",
            "input_bg": "#191D27",
        }
    return {
        "bg": "#F7F7FB", "surface": "#FFFFFF", "border": "#E5E7F0",
        "text": "#14161B", "text_muted": "#6B7280",
        "primary": "#6366F1", "primary_soft": "#EEF0FE",
        "green": "#16A34A", "green_soft": "#E7F8ED",
        "amber": "#D97706", "amber_soft": "#FDF3E2",
        "red": "#DC2626", "red_soft": "#FDEBEC",
        "on_accent": "#FFFFFF",
        "shadow": "0 1px 2px rgba(16,24,40,0.04), 0 6px 16px rgba(16,24,40,0.06)",
        "input_bg": "#FBFBFE",
    }


P = get_palette(st.session_state.theme)


# =====================================================================
# CSS — every component driven off the same palette
# =====================================================================

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700;800&family=Inter:wght@400;500;600&display=swap');

html, body, [class*="css"] {{ font-family: 'Inter', sans-serif !important; }}

.stApp {{ background: {P['bg']} !important; color: {P['text']} !important; }}
#MainMenu, footer, header[data-testid="stHeader"] {{ visibility: hidden; height: 0; }}

.block-container {{ padding-top: 1.6rem; padding-bottom: 3.5rem; max-width: 1040px; margin: 0 auto; }}

h1, h2, h3, h4, h5 {{ font-family: 'Sora', sans-serif !important; color: {P['text']} !important; }}
p, span, div {{ color: {P['text']}; }}

/* ---------- TOP BAR ---------- */
.topbar {{ display: flex; justify-content: flex-end; margin-bottom: 0.2rem; }}

/* ---------- HERO ---------- */
.hero {{ text-align: center; padding: 0.6rem 1rem 1.8rem 1rem; }}
.hero .eyebrow {{ font-size: 0.78rem; font-weight: 700; letter-spacing: 0.1em; color: {P['primary']}; text-transform: uppercase; margin-bottom: 0.6rem; }}
.hero h1 {{ font-size: 2.2rem; font-weight: 800; margin: 0.2rem auto 0.7rem auto; max-width: 700px; line-height: 1.25; }}
.hero p {{ color: {P['text_muted']} !important; font-size: 1rem; max-width: 560px; margin: 0 auto; }}

/* ---------- CARDS ---------- */
div[class*="st-key-card_"] {{
    background: {P['surface']} !important; border: 1px solid {P['border']} !important;
    border-radius: 16px !important; padding: 1.5rem 1.6rem !important; box-shadow: {P['shadow']} !important;
}}
div[class*="st-key-kpi_"] {{
    background: {P['surface']} !important; border: 1px solid {P['border']} !important;
    border-radius: 16px !important; padding: 1.1rem 1.3rem !important; box-shadow: {P['shadow']} !important;
    text-align: center;
}}

/* ---------- JOB DESCRIPTION TEXTAREA ---------- */
.stTextArea textarea {{
    background: {P['input_bg']} !important; color: {P['text']} !important;
    border: 1.5px solid {P['border']} !important; border-radius: 12px !important;
    padding: 14px 16px !important; font-size: 0.95rem !important; line-height: 1.55 !important;
    caret-color: {P['primary']} !important;
    resize: none !important; min-height: 130px !important;
    transition: height 0.08s ease-out;
}}
.stTextArea textarea::placeholder {{ color: {P['text_muted']} !important; }}
.stTextArea textarea:focus {{ border-color: {P['primary']} !important; box-shadow: 0 0 0 3px {P['primary_soft']} !important; }}

/* ---------- FILE UPLOADER ---------- */
[data-testid="stFileUploaderDropzone"] {{
    background: {P['input_bg']} !important; border: 1.5px dashed {P['border']} !important; border-radius: 12px !important;
}}
[data-testid="stFileUploaderDropzone"] * {{ color: {P['text_muted']} !important; }}

/* ---------- BUTTONS ---------- */
button[kind="primary"] {{
    background: {P['primary']} !important; border: none !important; color: {P['on_accent']} !important;
    font-family: 'Sora', sans-serif !important; font-weight: 700 !important; font-size: 0.92rem !important;
    border-radius: 10px !important; padding: 0.7rem 1.4rem !important;
}}
button[kind="secondary"] {{
    background: {P['surface']} !important; border: 1px solid {P['border']} !important; color: {P['text']} !important;
    font-weight: 600 !important; border-radius: 10px !important;
}}

/* ---------- SECTION HEADER ---------- */
.section-head {{ display: flex; align-items: center; justify-content: center; gap: 0.5rem; margin: 2.2rem 0 1.1rem 0; text-align: center; }}
.section-head h3 {{ margin: 0; font-size: 1.15rem; }}

/* ---------- KPI ---------- */
.kpi-value {{ font-family: 'Sora', sans-serif; font-size: 1.7rem; font-weight: 800; }}
.kpi-label {{ font-size: 0.8rem; color: {P['text_muted']} !important; font-weight: 600; margin-top: 0.2rem; }}
.kpi-bar {{ height: 4px; border-radius: 4px; margin: 0 auto 0.6rem auto; width: 40px; }}

/* ---------- BADGES ---------- */
.badge-row {{ display: flex; flex-wrap: wrap; gap: 0.55rem; }}
.badge {{
    display: inline-flex; align-items: center; gap: 0.35rem;
    background: {P['green_soft']}; color: {P['green']};
    border: 1px solid {P['green_soft']}; border-radius: 999px;
    padding: 0.4rem 0.85rem; font-size: 0.86rem; font-weight: 600;
}}

/* ---------- WARNING CARDS ---------- */
.warn-grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 0.6rem; }}
.warn-card {{
    background: {P['red_soft']}; border: 1px solid {P['red_soft']}; border-radius: 12px;
    padding: 0.65rem 0.8rem; font-size: 0.86rem; font-weight: 600; color: {P['red']};
    display: flex; align-items: center; gap: 0.45rem;
}}

/* ---------- INFO CARDS ---------- */
.info-card .card-header {{
    font-family: 'Sora', sans-serif; font-weight: 700; font-size: 0.98rem;
    padding-bottom: 0.7rem; margin-bottom: 0.7rem; border-bottom: 1px solid {P['border']};
    display: flex; align-items: center; gap: 0.5rem;
}}
.header-green {{ color: {P['green']} !important; }}
.header-amber {{ color: {P['amber']} !important; }}
.header-primary {{ color: {P['primary']} !important; }}
.header-red {{ color: {P['red']} !important; }}
.info-item {{ display: flex; gap: 0.6rem; padding: 0.42rem 0; font-size: 0.9rem; color: {P['text']}; }}
.dot-green {{ color: {P['green']}; font-weight: 800; }}
.dot-amber {{ color: {P['amber']}; font-weight: 800; }}
.dot-primary {{ color: {P['primary']}; font-family:'Sora',sans-serif; font-weight: 700; font-size:0.82rem; }}

/* ---------- CANDIDATE STRIP ---------- */
.candidate-strip {{
    display: flex; justify-content: space-between; align-items: center;
    background: {P['surface']}; border: 1px solid {P['border']}; border-radius: 16px;
    padding: 1.1rem 1.5rem; box-shadow: {P['shadow']}; margin-bottom: 0.3rem;
}}
.candidate-strip .name {{ font-family: 'Sora', sans-serif; font-weight: 800; font-size: 1.15rem; }}
.candidate-strip .email {{ color: {P['text_muted']} !important; font-size: 0.85rem; margin-top: 0.15rem; }}
.status-pill {{ background: {P['green_soft']}; color: {P['green']}; font-weight: 700; font-size: 0.78rem; padding: 0.35rem 0.75rem; border-radius: 999px; }}

/* ---------- ALERTS ---------- */
.alert-card {{ background: {P['red_soft']}; border: 1px solid {P['red_soft']}; border-radius: 14px; padding: 1rem 1.2rem; color: {P['red']}; font-size: 0.9rem; text-align: center; }}
.empty-card {{ background: {P['green_soft']}; border: 1px solid {P['green_soft']}; border-radius: 14px; padding: 1.3rem; color: {P['green']}; text-align: center; font-weight: 600; }}

@media (max-width: 640px) {{
    .hero h1 {{ font-size: 1.5rem; }}
    .block-container {{ padding-left: 1rem; padding-right: 1rem; }}
}}
</style>
""", unsafe_allow_html=True)


# =====================================================================
# HELPERS
# =====================================================================

def band_color(value: int) -> str:
    if value >= 70:
        return P["green"]
    if value >= 40:
        return P["amber"]
    return P["red"]


def make_gauge(value: int, title: str):
    color = band_color(value)
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=value,
            number={"font": {"family": "Sora", "size": 38, "color": P["text"]}},
            title={"text": title, "font": {"family": "Sora", "size": 16, "color": P["text_muted"]}},
            gauge={
                "axis": {"range": [0, 100], "tickfont": {"size": 10, "color": P["text_muted"]}},
                "bar": {"color": color, "thickness": 0.32},
                "bgcolor": P["bg"],
                "borderwidth": 0,
                "steps": [
                    {"range": [0, 40], "color": P["red_soft"]},
                    {"range": [40, 70], "color": P["amber_soft"]},
                    {"range": [70, 100], "color": P["green_soft"]},
                ],
            },
        )
    )
    fig.update_layout(
        height=260,
        margin=dict(l=25, r=25, t=55, b=15),
        paper_bgcolor="rgba(0,0,0,0)",
        font={"family": "Inter", "color": P["text"]},
    )
    return fig


def kpi_card(value, label, color):
    st.markdown(
        f'<div class="kpi-bar" style="background:{color};"></div>'
        f'<div class="kpi-value">{value}</div>'
        f'<div class="kpi-label">{label}</div>',
        unsafe_allow_html=True,
    )


def badges(items):
    if not items:
        return f"<span style='color:{P['text_muted']}; font-size:0.88rem;'>None found.</span>"
    return '<div class="badge-row">' + "".join(f'<span class="badge">✓ {html.escape(str(s))}</span>' for s in items) + "</div>"


def warning_cards(items):
    if not items:
        return f"<span style='color:{P['text_muted']}; font-size:0.88rem;'>None found.</span>"
    return '<div class="warn-grid">' + "".join(f'<div class="warn-card">⚠ {html.escape(str(s))}</div>' for s in items) + "</div>"


# =====================================================================
# TOP BAR — theme toggle
# =====================================================================

top_l, top_r = st.columns([6, 1])
with top_r:
    toggle_label = "🌙 Dark" if st.session_state.theme == "light" else "☀️ Light"
    if st.button(toggle_label, key="theme_toggle", use_container_width=True):
        st.session_state.theme = "dark" if st.session_state.theme == "light" else "light"
        st.rerun()


# =====================================================================
# HERO
# =====================================================================

st.markdown("""
<div class="hero">
    <div class="eyebrow">AI-Powered · ATS Insights</div>
    <h1>See your resume the way an ATS sees it.</h1>
    <p>Upload your resume and paste a job description to get an instant match score,
    skill gap breakdown, and concrete suggestions to improve your chances.</p>
</div>
""", unsafe_allow_html=True)


# =====================================================================
# INPUT
# =====================================================================

col_a, col_b = st.columns(2, gap="medium")

with col_a:
    with st.container(key="card_upload"):
        st.markdown("##### 📄 Resume (PDF)")
        uploaded_file = st.file_uploader(
            "Upload resume", type=["pdf"], label_visibility="collapsed",
        )
        if uploaded_file:
            st.markdown(
                f'<div style="margin-top:0.6rem; font-size:0.85rem; color:{P["green"]}; font-weight:600;">'
                f'✓ {uploaded_file.name} uploaded</div>',
                unsafe_allow_html=True,
            )

with col_b:
    with st.container(key="card_jd"):
        st.markdown("##### 🎯 Job Description")

        job_description = st.text_area(
            "Job description",
            height=130,
            label_visibility="collapsed",
            placeholder="Paste the full job description here...",
            key="job_description_input",
        )
        st.markdown(
            f'<div style="font-size:0.75rem; color:{P["text_muted"]}; margin-top:0.4rem;">'
            f'Grows automatically as the description gets longer.</div>',
            unsafe_allow_html=True,
        )

        # st.components.v1.html(
        #     """
        #     <script>
        #     (function() {
        #         const MIN_H = 130, MAX_H = 640;
        #         function resize(ta) {
        #             ta.style.height = 'auto';
        #             const h = Math.min(Math.max(ta.scrollHeight + 4, MIN_H), MAX_H);
        #             ta.style.height = h + 'px';
        #             ta.style.overflowY = ta.scrollHeight > MAX_H ? 'auto' : 'hidden';
        #         }
        #         function attach() {
        #             const doc = window.parent.document;
        #             const ta = doc.querySelector('textarea[aria-label="Job description"]');
        #             if (!ta) { setTimeout(attach, 250); return; }
        #             resize(ta);
        #             if (ta.dataset.autogrowAttached) return;
        #             ta.dataset.autogrowAttached = "true";
        #             ta.addEventListener('input', function() { resize(ta); });
        #             new ResizeObserver(function() { resize(ta); }).observe(ta);
        #         }
        #         attach();
        #     })();
        #     </script>
        #     """,
        #     height=0,
        # )

st.write("")
_, mid, _ = st.columns([1, 1.2, 1])
with mid:
    run_scan = st.button("Analyze Resume", type="primary", use_container_width=True)


# =====================================================================
# RESULTS
# =====================================================================

if run_scan:
    if not (uploaded_file and job_description):
        st.markdown(
            '<div class="alert-card">Please upload a resume and paste a job description '
            'before running the analysis.</div>',
            unsafe_allow_html=True,
        )
    else:
        with st.spinner("Analyzing your resume..."):
            try:
                result = analyze_resume(uploaded_file, job_description)
                st.session_state["analysis_result"] = result
            except Exception as e:
                result = None
                st.markdown(
                    f'<div class="alert-card"><strong>Analysis failed.</strong><br>'
                    f'The response could not be parsed. Please try again.<br>'
                    f'<span style="font-size:0.78rem;">{safe_error_message(e)}</span></div>',
                    unsafe_allow_html=True,
                )

        if result:
            st.markdown(
                f"""
                <div class="candidate-strip">
                    <div>
                        <div class="name">{html.escape(result.get('name') or 'Candidate')}</div>
                        <div class="email">{html.escape(result.get('email') or 'No email extracted')}</div>
                    </div>
                    <div class="status-pill">✓ Analysis complete</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

            ats = result["ats_score"]
            match = result["match_percentage"]
            matching_skills = result["matching_skills"]
            missing_skills = result["missing_skills"]

            # ---------- KPI ROW ----------
            st.markdown('<div style="height:1.4rem;"></div>', unsafe_allow_html=True)
            k1, k2, k3, k4 = st.columns(4, gap="medium")
            with k1:
                with st.container(key="kpi_ats"):
                    kpi_card(ats, "ATS Score", band_color(ats))
            with k2:
                with st.container(key="kpi_match"):
                    kpi_card(f"{match}%", "Match Percentage", band_color(match))
            with k3:
                with st.container(key="kpi_matching"):
                    kpi_card(len(matching_skills), "Matching Skills", P["green"])
            with k4:
                with st.container(key="kpi_missing"):
                    kpi_card(len(missing_skills), "Missing Skills", P["red"])

            # ---------- SCORE DASHBOARD ----------
            st.markdown('<div class="section-head"><h3>Score Dashboard</h3></div>', unsafe_allow_html=True)
            g1, g2 = st.columns(2, gap="medium")
            with g1:
                with st.container(key="card_gauge1"):
                    st.plotly_chart(make_gauge(ats, "ATS SCORE"), use_container_width=True, config={"displayModeBar": False})
            with g2:
                with st.container(key="card_gauge2"):
                    st.plotly_chart(make_gauge(match, "MATCH %"), use_container_width=True, config={"displayModeBar": False})

            # ---------- SKILLS ----------
            st.markdown('<div class="section-head"><h3>Skills Breakdown</h3></div>', unsafe_allow_html=True)
            s1, s2 = st.columns(2, gap="medium")
            with s1:
                with st.container(key="card_matching"):
                    st.markdown('<div class="card-header header-green">✅ Matching Skills</div>', unsafe_allow_html=True)
                    st.markdown(badges(matching_skills), unsafe_allow_html=True)
            with s2:
                with st.container(key="card_missing"):
                    st.markdown('<div class="card-header header-red">⚠️ Missing Skills</div>', unsafe_allow_html=True)
                    st.markdown(warning_cards(missing_skills), unsafe_allow_html=True)

            # ---------- STRENGTHS / WEAKNESSES / SUGGESTIONS ----------
            st.markdown('<div class="section-head"><h3>Strengths, Weaknesses &amp; Suggestions</h3></div>', unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3, gap="medium")
            with c1:
                with st.container(key="card_strengths"):
                    st.markdown('<div class="card-header header-green">💪 Strengths</div>', unsafe_allow_html=True)
                    items = "".join(f'<div class="info-item"><span class="dot-green">●</span> {html.escape(str(s))}</div>' for s in result.get("strengths", []))
                    st.markdown(items or f"<span style='color:{P['text_muted']};'>None listed.</span>", unsafe_allow_html=True)
            with c2:
                with st.container(key="card_weaknesses"):
                    st.markdown('<div class="card-header header-amber">⚠️ Weaknesses</div>', unsafe_allow_html=True)
                    items = "".join(f'<div class="info-item"><span class="dot-amber">●</span> {html.escape(str(w))}</div>' for w in result.get("weaknesses", []))
                    st.markdown(items or f"<span style='color:{P['text_muted']};'>None listed.</span>", unsafe_allow_html=True)
            with c3:
                with st.container(key="card_suggestions"):
                    st.markdown('<div class="card-header header-primary">💡 Suggestions</div>', unsafe_allow_html=True)
                    items = "".join(
                        f'<div class="info-item"><span class="dot-primary">{i+1:02d}</span> {html.escape(str(s))}</div>'
                        for i, s in enumerate(result.get("suggestions", []))
                    )
                    st.markdown(items or f"<span style='color:{P['text_muted']};'>None listed.</span>", unsafe_allow_html=True)

            # ---------- MISSING SKILLS CHART ----------
            st.markdown('<div class="section-head"><h3>Missing Skills — Gap Analysis</h3></div>', unsafe_allow_html=True)
            if missing_skills:
                df = pd.DataFrame({
                    "Skill": missing_skills[::-1],
                    "Gap": [len(missing_skills) - i for i in range(len(missing_skills))][::-1],
                })
                on_accent = P["on_accent"]
                fig = px.bar(
                    df, x="Gap", y="Skill", orientation="h", text="Skill",
                    hover_data={"Gap": False, "Skill": False},
                )
                fig.update_traces(
                    marker_color=P["red"],
                    textposition="inside",
                    insidetextanchor="start",
                    textfont=dict(color=on_accent, family="Inter", size=13),
                    hovertemplate="<b>%{y}</b><extra></extra>",
                )
                fig.update_layout(
                    height=90 + 46 * len(missing_skills),
                    showlegend=False,
                    plot_bgcolor="rgba(0,0,0,0)",
                    paper_bgcolor="rgba(0,0,0,0)",
                    font={"family": "Inter", "color": P["text"]},
                    xaxis={"visible": False},
                    yaxis={"visible": False, "categoryorder": "array", "categoryarray": df["Skill"]},
                    margin=dict(t=10, b=10, l=10, r=10),
                    bargap=0.35,
                )
                with st.container(key="card_chart"):
                    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            else:
                st.markdown(
                    '<div class="empty-card">🎉 No missing skills found — this resume fully '
                    'covers the role requirements.</div>',
                    unsafe_allow_html=True,
                )

            # ---------- EXPORT REPORT ----------
            st.markdown('<div class="section-head"><h3>Export Report</h3></div>', unsafe_allow_html=True)
            safe_name = (result.get("name") or "candidate").strip().replace(" ", "_") or "candidate"
            resume_filename = uploaded_file.name if uploaded_file else "resume.pdf"

            exp1, exp2 = st.columns(2, gap="medium")
            with exp1:
                with st.container(key="card_export_pdf"):
                    try:
                        pdf_bytes = generate_pdf_bytes(result, resume_filename)
                        st.download_button(
                            "⬇️ Download PDF Report",
                            data=pdf_bytes,
                            file_name=f"ats_report_{safe_name}.pdf",
                            mime="application/pdf",
                            use_container_width=True,
                        )
                    except Exception as e:
                        st.markdown(
                            f'<div class="alert-card">PDF export failed.<br>'
                            f'<span style="font-size:0.78rem;">{safe_error_message(e)}</span></div>',
                            unsafe_allow_html=True,
                        )

            with exp2:
                with st.container(key="card_export_docx"):
                    try:
                        docx_bytes = generate_docx_bytes(result, resume_filename)
                        st.download_button(
                            "⬇️ Download Word Report",
                            data=docx_bytes,
                            file_name=f"ats_report_{safe_name}.docx",
                            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            use_container_width=True,
                        )
                    except Exception as e:
                        st.markdown(
                            f'<div class="alert-card">DOCX export failed.<br>'
                            f'<span style="font-size:0.78rem;">{safe_error_message(e)}</span></div>',
                            unsafe_allow_html=True,
                        )

# =====================================================================
# GENERATE OPTIMIZED RESUME
# =====================================================================

st.markdown('<div class="section-head"><h3>Generate Optimized Resume</h3></div>', unsafe_allow_html=True)

with st.container(key="card_optimize"):
    st.markdown(
        f'<div style="font-size:0.85rem; color:{P["text_muted"]}; margin-bottom:0.9rem;">'
        f'Rewrites your resume to align with this job description, using only what\'s '
        f'already in your resume — it will not invent skills, employers, or metrics.</div>',
        unsafe_allow_html=True,
    )

    if st.button("🚀 Generate Optimized Resume", type="primary", use_container_width=True, key="optimize_btn"):
        analysis_result = st.session_state.get("analysis_result")

        if uploaded_file is None:
            st.error("Please upload your resume first.")
        elif not job_description.strip():
            st.error("Please enter the Job Description first.")
        elif not analysis_result:
            st.error("Please click 'Analyze Resume' first.")
        else:
            try:
                with st.spinner("Rewriting your resume for this job..."):
                    uploaded_file.seek(0)
                    resume_text = extract_resume_text(uploaded_file)
                    if not resume_text.strip():
                        raise ValueError("Could not extract text from the uploaded resume.")

                    optimized = generate_optimized_resume(
                        resume_text, job_description, analysis_result,
                    )

                st.session_state["optimized_resume"] = optimized
                st.session_state["optimized_candidate_name"] = (
                    optimized.get("name") or analysis_result.get("name") or "Candidate"
                )
                st.success("✅ Optimized Resume Generated!")

            except Exception as e:
                st.session_state["optimized_resume"] = None
                st.error(f"Unable to generate optimized resume: {safe_error_message(e)}")

    # =================================================================
    # SHOW OPTIMIZED RESUME
    # =================================================================
    optimized = st.session_state.get("optimized_resume")

    if optimized:
        st.markdown('<div style="height:0.8rem;"></div>', unsafe_allow_html=True)

        target_role = optimized.get("target_role") or "Target Job"
        st.markdown(
            f'<div class="status-pill" style="display:inline-block; margin-bottom:0.9rem;">'
            f'✓ Optimized for {html.escape(target_role)}</div>',
            unsafe_allow_html=True,
        )

        matched = optimized.get("keywords_matched") or []
        st.markdown('<div class="card-header header-green">✅ Keywords Matched</div>', unsafe_allow_html=True)
        st.markdown(badges(matched), unsafe_allow_html=True)

        added = optimized.get("keywords_added") or []
        if added:
            st.markdown(
                '<div class="card-header header-primary" style="margin-top:0.9rem;">'
                '✨ Skills Surfaced (already in your resume, now clearer)</div>',
                unsafe_allow_html=True,
            )
            st.markdown(badges(added), unsafe_allow_html=True)

        still_missing = optimized.get("missing_keywords") or []
        st.markdown(
            '<div class="card-header header-red" style="margin-top:0.9rem;">'
            '⚠️ Still Missing — not added to your resume</div>',
            unsafe_allow_html=True,
        )
        st.markdown(warning_cards(still_missing), unsafe_allow_html=True)

        notes = optimized.get("optimization_notes") or []
        if notes:
            st.markdown('<div class="card-header header-primary" style="margin-top:0.9rem;">📝 What Changed</div>', unsafe_allow_html=True)
            note_items = "".join(
                f'<div class="info-item"><span class="dot-primary">{i + 1:02d}</span> {html.escape(str(n))}</div>'
                for i, n in enumerate(notes)
            )
            st.markdown(note_items, unsafe_allow_html=True)

        # Preview Expander
        with st.expander("📄 Preview Optimized Resume", expanded=True):
            cand_name = optimized.get('name') or st.session_state.get('optimized_candidate_name') or 'Candidate'
            st.markdown(f"**Name:** {cand_name}")
            summary_txt = optimized.get('professional_summary') or optimized.get('summary') or ''
            if summary_txt:
                st.markdown(f"**Summary:** {summary_txt}")

            skills = optimized.get("technical_skills") or {}
            if skills:
                st.markdown("### Skills")
                for category, items in skills.items():
                    if items:
                        if isinstance(items, list):
                            st.markdown(f"**{category}:** {', '.join(items)}")
                        else:
                            st.markdown(f"**{category}:** {items}")

            experience = optimized.get("experience") or []
            if experience:
                st.markdown("### Experience")
                for entry in experience:
                    header = " — ".join(p for p in [entry.get("title"), entry.get("company")] if p)
                    if header:
                        st.markdown(f"**{header}**")
                    duration = entry.get("duration") or entry.get("dates") or ""
                    if duration:
                        st.markdown(f"_{duration}_")
                    for bullet in entry.get("bullets") or []:
                        st.markdown(f"- {bullet}")

            projects = optimized.get("projects") or []
            if projects:
                st.markdown("### Projects")
                for project in projects:
                    p_name = project.get('name') or project.get('title') or ''
                    if p_name:
                        st.markdown(f"**{p_name}**")
                    for bullet in project.get("bullets") or []:
                        st.markdown(f"- {bullet}")

            education = optimized.get("education") or []
            if education:
                st.markdown("### Education")
                for item in education:
                    degree = item.get("degree", "")
                    institution = item.get("institution", "")
                    dates = item.get("dates", "")
                    parts = [v for v in [degree, institution, dates] if v]
                    if parts:
                        st.markdown(" — ".join(parts))

            certifications = optimized.get("certifications") or []
            if certifications:
                st.markdown("### Certifications")
                for cert in certifications:
                    st.markdown(f"- {cert}")

        # Download Optimized Resume
        try:
            candidate_name = st.session_state.get("optimized_candidate_name") or optimized.get("name") or "Candidate"
            opt_pdf_bytes = generate_optimized_resume_pdf(optimized, candidate_name)
            safe_cname = candidate_name.strip().lower().replace(" ", "_") or "candidate"

            st.download_button(
                "⬇️ Download Optimized Resume",
                data=opt_pdf_bytes,
                file_name=f"optimized_resume_{safe_cname}.pdf",
                mime="application/pdf",
                use_container_width=True,
                key="download_optimized_resume_pdf",
            )
        except Exception as e:
            st.markdown(
                f'<div class="alert-card">PDF generation failed.<br>'
                f'<span style="font-size:0.78rem;">{safe_error_message(e)}</span></div>',
                unsafe_allow_html=True,
            )
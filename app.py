import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd

from main import analyze_resume


st.title("🤖 AI Resume Analyzer")


uploaded_file = st.file_uploader(
    "Upload your Resume PDF",
    type=["pdf"]
)


job_description = st.text_area(
    "Paste Job Description"
)


if uploaded_file:
    st.success("Resume uploaded successfully ✅")


if st.button("Analyze Resume"):

    if uploaded_file and job_description:

        with st.spinner("🤖 AI is analyzing your resume..."):

            result = analyze_resume(
                uploaded_file,
                job_description
            )


        st.success("Analysis Completed ✅")


        # Resume Analysis

        st.subheader("📊 Resume Analysis")


        st.write(
            f"Candidate Name: {result['name']}"
        )


               # ==============================
        # Gauge Dashboard
        # ==============================

        st.subheader("🎯 Resume Score Dashboard")


        ats = result["ats_score"]
        match = result["match_percentage"]


        col1, col2 = st.columns(2)


        with col1:

            ats_fig = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=ats,
                    title={
                        "text": "ATS Score"
                    },
                    gauge={
                        "axis": {
                            "range": [0,100]
                        }
                    }
                )
            )


            ats_fig.update_layout(
                height=300
            )


            st.plotly_chart(
                ats_fig,
                use_container_width=True
            )



        with col2:

            match_fig = go.Figure(
                go.Indicator(
                    mode="gauge+number",
                    value=match,
                    title={
                        "text": "Match Percentage"
                    },
                    gauge={
                        "axis": {
                            "range": [0,100]
                        }
                    }
                )
            )


            match_fig.update_layout(
                height=300
            )


            st.plotly_chart(
                match_fig,
                use_container_width=True
            )


        # Matching Skills

        st.subheader("✅ Matching Skills")

        for skill in result["matching_skills"]:
            st.success(skill)



        # Missing Skills

        st.subheader("❌ Missing Skills")

        for skill in result["missing_skills"]:
            st.error(skill)



        # Strengths

        st.subheader("💪 Strengths")

        for strength in result["strengths"]:
            st.success(strength)



        # Weaknesses

        st.subheader("⚠️ Weaknesses")

        for weakness in result["weaknesses"]:
            st.warning(weakness)



        # Suggestions

        st.subheader("💡 Suggestions")

        for suggestion in result["suggestions"]:
            st.info(suggestion)



        # Missing Skills Chart

        st.subheader("📊 Missing Skills Analysis")


        missing_skills = result["missing_skills"]


        if missing_skills:

            df = pd.DataFrame(
                {
                    "Skills": missing_skills,
                    "Gap": [100] * len(missing_skills)
                }
            )


            fig = px.bar(
                df,
                x="Skills",
                y="Gap",
                title="Missing Skills Gap",
                text="Skills"
            )


            st.plotly_chart(fig)


        else:

            st.success(
                "No missing skills found 🎉"
            )


    else:

        st.warning(
            "Please upload resume and add job description"
        )
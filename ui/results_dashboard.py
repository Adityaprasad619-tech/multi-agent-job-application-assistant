"""
Results Dashboard Component
=============================
Streamlit UI component to display the CompleteApplicationPackage structured outputs.

Design Decisions:
- Clean tabs for different packages: ATS & Gap Analysis, Job Analysis, Resume & Cover Letter, Outreach Messages.
- Visual elements such as tags/badges for skills and ATS keywords.
- Dynamic PDF export generators mapped straight to ReportLab services via st.download_button().
- Robust formatting using columns, metrics, and progress bars.
"""

from __future__ import annotations

import streamlit as st
from schemas.agent_outputs import CompleteApplicationPackage
from services.export_service import ExportService


def render_results_dashboard(
    package: CompleteApplicationPackage,
    job_title: str = "Target Job",
    organization: str = "Hiring Agency",
) -> None:
    """
    Render the complete job application package in tabs.

    Parameters
    ----------
    package : CompleteApplicationPackage
        The structured output package containing analysis, resume recommendations,
        cover letter, and networking outreach messages.
    job_title : str
        Target job position title.
    organization : str
        Target hiring organization/company.
    """
    st.markdown("### Tailored Application Suite")
    st.markdown(
        "Below are your bespoke analysis, resume enhancements, gap metrics, and outreach templates."
    )

    # ------------------------------------------------------------------
    # TABS DESIGN
    # ------------------------------------------------------------------
    tabs = ["ATS & Gap Analysis", "Job Analysis", "Resume & Cover Letter", "Networking & Outreach"]
    tab_ats, tab_analysis, tab_resume, tab_outreach = st.tabs(tabs)

    # ------------------------------------------------------------------
    # TAB 1: ATS & GAP ANALYSIS
    # ------------------------------------------------------------------
    with tab_ats:
        st.subheader("ATS Match Metrics & Resume Insights")

        if package.ats_score:
            score = package.ats_score.ats_score
            
            # Metric + Progress representation
            col_metric, col_progress = st.columns([1, 3])
            with col_metric:
                st.metric(
                    label="ATS Match Rating",
                    value=f"{score}%",
                    delta="Good Match" if score >= 75 else "Requires Tailoring" if score >= 50 else "Weak Match",
                    delta_color="normal" if score >= 75 else "off",
                )
            with col_progress:
                st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)
                st.progress(score / 100)
                st.caption(f"Calculated by comparing required skills against parsed resume content.")

            st.markdown("---")

            # Matched, Partially Matched, & Missing Keywords
            col_match, col_partial, col_miss = st.columns(3)
            with col_match:
                st.markdown("#### Matched Skills")
                if package.ats_score.matched_keywords:
                    match_html = " ".join(
                        [
                            f"<span style='background-color: #22c55e22; color: #15803d; "
                            f"padding: 4px 10px; border-radius: 12px; margin-right: 6px; "
                            f"font-size: 0.85em; font-weight: 600; display: inline-block; "
                            f"margin-bottom: 6px;'>{kw}</span>"
                            for kw in package.ats_score.matched_keywords
                        ]
                    )
                    st.markdown(match_html, unsafe_allow_html=True)
                else:
                    st.caption("No direct keyword matches found.")

            with col_partial:
                st.markdown("#### Partially Matched Skills")
                if package.ats_score.partially_matched_keywords:
                    for pm in package.ats_score.partially_matched_keywords:
                        via_text = ", ".join(pm.matched_via)
                        partial_html = (
                            f"<div style='background-color: #f59e0b18; border-left: 3px solid #d97706; "
                            f"padding: 8px 12px; border-radius: 6px; margin-bottom: 8px;'>"
                            f"<span style='color: #92400e; font-weight: 600; font-size: 0.9em;'>"
                            f"{pm.required_skill}</span><br/>"
                            f"<span style='color: #78716c; font-size: 0.8em;'>via {via_text}</span></div>"
                        )
                        st.markdown(partial_html, unsafe_allow_html=True)
                else:
                    st.caption("No partial matches detected.")

            with col_miss:
                st.markdown("#### Missing Skills")
                if package.ats_score.missing_keywords:
                    miss_html = " ".join(
                        [
                            f"<span style='background-color: #ef444422; color: #b91c1c; "
                            f"padding: 4px 10px; border-radius: 12px; margin-right: 6px; "
                            f"font-size: 0.85em; font-weight: 600; display: inline-block; "
                            f"margin-bottom: 6px;'>{kw}</span>"
                            for kw in package.ats_score.missing_keywords
                        ]
                    )
                    st.markdown(miss_html, unsafe_allow_html=True)
                else:
                    st.success("No required keywords are missing.")

            # Specific Recommendations from the ATS Matcher
            if package.ats_score.recommendations:
                st.markdown("#### Quick Optimization Steps")
                for rec in package.ats_score.recommendations:
                    st.markdown(f"- {rec}")

            st.markdown("---")

        # Resume standalone analysis (if present)
        if package.resume_analysis:
            st.markdown("#### Extracted Candidate Profile")
            col_years, col_edu = st.columns(2)
            with col_years:
                st.markdown(f"**Estimated Experience:** {package.resume_analysis.years_of_experience}")
            with col_edu:
                st.markdown(f"**Education Summary:** {package.resume_analysis.education_summary}")

            c_str, c_weak = st.columns(2)
            with c_str:
                st.markdown("**Core Career Strengths:**")
                for s in package.resume_analysis.strengths:
                    st.markdown(f"- {s}")
            with c_weak:
                st.markdown("**Perceived Profile Gaps:**")
                for w in package.resume_analysis.weaknesses:
                    st.markdown(f"- {w}")

            st.markdown("---")

        # Gap analysis results
        if package.gap_analysis:
            st.markdown("#### Specialist Gap Analysis")
            g_match, g_miss = st.columns(2)
            with g_match:
                st.markdown("**Matching Skills:**")
                if package.gap_analysis.matching_skills:
                    for skill in package.gap_analysis.matching_skills:
                        st.markdown(f"- {skill}")
                else:
                    st.caption("No matching skills recorded.")
            with g_miss:
                st.markdown("**Missing/Weak Competencies:**")
                if package.gap_analysis.missing_skills:
                    for skill in package.gap_analysis.missing_skills:
                        st.markdown(f"- {skill}")
                else:
                    st.caption("No missing skills recorded.")

            if package.gap_analysis.improvement_recommendations:
                st.markdown("**Career Coach Tailoring Tips:**")
                for rec in package.gap_analysis.improvement_recommendations:
                    st.markdown(f"- {rec}")

    # ------------------------------------------------------------------
    # TAB 2: JOB ANALYSIS
    # ------------------------------------------------------------------
    with tab_analysis:
        st.subheader("Core Job Analysis & Insights")

        # Role Summary
        st.markdown("#### Role Summary")
        st.info(package.analysis.role_summary)

        # Columns for Skills & Keywords
        col1, col2 = st.columns(2)

        with col1:
            st.markdown("#### Required Technical Skills")
            if package.analysis.required_skills:
                for skill in package.analysis.required_skills:
                    st.markdown(f"- **{skill}**")
            else:
                st.caption("No required skills explicitly listed.")

            st.markdown("#### Preferred Qualifications")
            if package.analysis.preferred_skills:
                for skill in package.analysis.preferred_skills:
                    st.markdown(f"- {skill}")
            else:
                st.caption("No preferred skills explicitly listed.")

        with col2:
            st.markdown("#### Recommended ATS Keywords")
            if package.analysis.ats_keywords:
                kw_html = " ".join(
                    [
                        f"<span style='background-color: #3b82f622; color: #3b82f6; "
                        f"padding: 4px 8px; border-radius: 12px; margin-right: 6px; "
                        f"font-size: 0.85em; font-weight: 500; display: inline-block; "
                        f"margin-bottom: 6px;'>{kw}</span>"
                        for kw in package.analysis.ats_keywords
                    ]
                )
                st.markdown(kw_html, unsafe_allow_html=True)
            else:
                st.caption("No ATS keywords generated.")

            st.markdown("#### Experience Requirements")
            st.warning(package.analysis.experience_requirements)

    # ------------------------------------------------------------------
    # TAB 3: RESUME & COVER LETTER
    # ------------------------------------------------------------------
    with tab_resume:
        c_hdr, c_dl = st.columns([3, 1])
        with c_hdr:
            st.subheader("Tailored Resume & Cover Letter Advice")
        with c_dl:
            # Generate export PDFs in-memory
            try:
                cl_pdf = ExportService.generate_cover_letter_pdf(
                    job_title=job_title,
                    organization=organization,
                    content=package.resume_package.cover_letter,
                )
                st.download_button(
                    label="Download PDF Pack",
                    data=cl_pdf,
                    file_name=f"Cover_Letter_{organization.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as exc:
                st.caption(f"Export loading error: {exc}")

        # Professional Summary Recommendation
        st.markdown("#### Suggested Professional Summary")
        st.markdown(
            "> " + package.resume_package.professional_summary.replace("\n", "\n> ")
        )

        st.markdown("---")

        # Resume recommendations and download buttons
        st.markdown("#### Actionable Resume Modifications")
        col_rec_title, col_rec_dl = st.columns([3, 1])
        with col_rec_title:
            st.caption("Implement these targeted adjustments in your core resume.")
        with col_rec_dl:
            try:
                rec_pdf = ExportService.generate_recommendations_pdf(
                    job_title=job_title,
                    organization=organization,
                    recommendations=package.resume_package.resume_recommendations,
                    professional_summary=package.resume_package.professional_summary,
                )
                st.download_button(
                    label="Download Guide PDF",
                    data=rec_pdf,
                    file_name=f"Tailoring_Guide_{organization.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as exc:
                st.caption(f"Export loading error: {exc}")

        if package.resume_package.resume_recommendations:
            for rec in package.resume_package.resume_recommendations:
                st.markdown(f"- {rec}")
        else:
            st.caption("No recommendations generated.")

        st.markdown("---")

        # Cover Letter
        st.markdown("#### Tailored Cover Letter")
        st.caption("Copy this text and use it as your draft.")
        st.text_area(
            label="Cover Letter Draft",
            value=package.resume_package.cover_letter,
            height=400,
            disabled=False,
            label_visibility="collapsed",
        )

    # ------------------------------------------------------------------
    # TAB 4: NETWORKING & OUTREACH
    # ------------------------------------------------------------------
    with tab_outreach:
        col_out_hdr, col_out_dl = st.columns([3, 1])
        with col_out_hdr:
            st.subheader("Personalized Networking Messages")
            st.markdown(
                "Use these customized templates to reach out to recruiters and professionals."
            )
        with col_out_dl:
            try:
                out_pdf = ExportService.generate_outreach_pdf(
                    job_title=job_title,
                    organization=organization,
                    linkedin_msg=package.outreach_package.linkedin_message,
                    recruiter_email=package.outreach_package.recruiter_message,
                    followup_msg=package.outreach_package.followup_message,
                )
                st.download_button(
                    label="Download Outreach PDF",
                    data=out_pdf,
                    file_name=f"Outreach_Kit_{organization.replace(' ', '_')}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                )
            except Exception as exc:
                st.caption(f"Export loading error: {exc}")

        # 1. LinkedIn Message
        st.markdown("#### LinkedIn Connection Note")
        st.caption(
            f"Under 300 characters. Character count: {len(package.outreach_package.linkedin_message)}"
        )
        st.code(package.outreach_package.linkedin_message, language="text")

        st.markdown("---")

        # 2. Recruiter Outreach
        st.markdown("#### Recruiter Outreach Email")
        st.code(package.outreach_package.recruiter_message, language="text")

        st.markdown("---")

        # 3. Follow-Up Message
        st.markdown("#### Follow-up message (5-7 days later)")
        st.code(package.outreach_package.followup_message, language="text")

"""
Multi-Agent Job Search System — Main Streamlit Entry Point
===========================================================
Run with:  streamlit run app.py

Flow:
  1. Initialize config, logging, DB, services.
  2. If user is not authenticated → show login/register page.
  3. If authenticated → show the main job search dashboard.
  4. Integration with CrewAI orchestrator for tailoring materials.
  5. Multi-user isolation and persistence using SQLite.
"""

from __future__ import annotations

from datetime import datetime, timezone
import streamlit as st

from utils.config import load_config
from utils.logger import setup_logger
from database.db_manager import DatabaseManager
from services.usajobs_service import USAJobsService
from auth.local_provider import LocalAuthProvider
from auth.session import get_current_user, is_authenticated, logout
from schemas.agent_outputs import (
    CompleteApplicationPackage,
    JobAnalysisOutput,
    ResumeOutput,
    OutreachOutput,
)
from schemas.resume_analysis import ResumeAnalysis
from schemas.ats_score import ATSScore
from schemas.gap_analysis import GapAnalysis
from services.usajobs_service import JobListing

st.set_page_config(
    page_title="Job Application Assistant",
    layout="wide",
    initial_sidebar_state="expanded",
)


@st.cache_resource
def init_app():
    """Load config, set up logging, and initialize services."""
    config = load_config()
    setup_logger(config.log_dir)
    db = DatabaseManager(config.db_path)
    usajobs = USAJobsService(config.usajobs_api_key, config.usajobs_email)

    # Initialize auth provider based on config
    if config.auth_provider == "clerk":
        from auth.clerk_provider import ClerkAuthProvider
        auth = ClerkAuthProvider(db, config.clerk_secret_key, config.clerk_publishable_key)
    else:
        auth = LocalAuthProvider(db)

    return config, db, usajobs, auth


config, db, usajobs, auth = init_app()

# ------------------------------------------------------------------
# AUTH GATE — show login page if not authenticated
# ------------------------------------------------------------------
if not is_authenticated():
    from ui.auth_page import render_auth_page
    render_auth_page(auth)
    st.stop()

# ------------------------------------------------------------------
# AUTHENTICATED — Main Dashboard
# ------------------------------------------------------------------
user = get_current_user()
if not user:
    st.warning("Session expired. Please sign in again.")
    logout()
    st.stop()

# Load cached resume profile from database if authenticated and not in session state
if "resume_profile" not in st.session_state:
    try:
        from schemas.resume_profile import StructuredResumeProfile
        stored_profile_json = db.get_resume_profile(user.id)
        if stored_profile_json:
            st.session_state["resume_profile"] = StructuredResumeProfile.model_validate_json(stored_profile_json)
            st.session_state["resume_filename"] = "Stored Profile (from Database)"
    except Exception as exc:
        st.error(f"Error loading stored resume profile: {exc}")



def load_application_data(app_id: int) -> tuple[CompleteApplicationPackage, JobListing]:
    """Helper to retrieve and deserialize complete application package from DB."""
    full_app = db.get_full_application(app_id)
    if not full_app or "outputs" not in full_app:
        raise ValueError("Application record not found or has no outputs.")

    outputs = full_app["outputs"]
    analysis = JobAnalysisOutput.model_validate_json(outputs["analysis"])
    resume = ResumeOutput.model_validate_json(outputs["resume_package"])
    outreach = OutreachOutput.model_validate_json(outputs["outreach_package"])

    # Safely load optional/new components for backwards compatibility
    resume_analysis = None
    if "resume_analysis" in outputs:
        resume_analysis = ResumeAnalysis.model_validate_json(outputs["resume_analysis"])

    ats_score = None
    if "ats_score" in outputs:
        ats_score = ATSScore.model_validate_json(outputs["ats_score"])

    gap_analysis = None
    if "gap_analysis" in outputs:
        gap_analysis = GapAnalysis.model_validate_json(outputs["gap_analysis"])

    loaded_package = CompleteApplicationPackage(
        analysis=analysis,
        resume_package=resume,
        outreach_package=outreach,
        resume_analysis=resume_analysis,
        ats_score=ats_score,
        gap_analysis=gap_analysis,
    )

    loaded_job = JobListing(
        position_id=str(full_app.get("id", "")),
        title=full_app["job_title"],
        organization=full_app["organization"],
        department="",
        location="",
        salary_min="0",
        salary_max="0",
        pay_interval="",
        grade_low="",
        grade_high="",
        position_url=full_app.get("job_url", ""),
        open_date="",
        close_date="",
        description=full_app.get("job_description", ""),
        qualifications="",
        who_may_apply="",
    )
    return loaded_package, loaded_job


# Sidebar Layout
with st.sidebar:
    st.title("Job Application Assistant")
    st.markdown("---")
    st.markdown(f"**{user.full_name}**")
    st.caption(user.email)
    if st.button("Sign Out", use_container_width=True):
        logout()
        # Clear active views
        st.session_state.pop("active_package", None)
        st.session_state.pop("active_job", None)
        st.session_state.pop("active_app_id", None)
        st.session_state.pop("resume_text", None)
        st.session_state.pop("resume_filename", None)
        st.session_state.pop("resume_profile", None)
        st.rerun()

    st.markdown("---")
    st.markdown("**Workflow:** Upload Resume → Search → Analyze")
    st.caption(f"Model: `{config.groq_model_name}`")
    st.caption(f"Test Mode: `{config.test_mode}`")

    # Sidebar History section
    st.markdown("---")
    st.subheader("My Applications")
    history_apps = db.get_applications(limit=20, user_id=user.id)
    if history_apps:
        for app_item in history_apps:
            date_str = ""
            try:
                dt = datetime.fromisoformat(app_item["created_at"])
                date_str = dt.strftime("%b %d, %Y")
            except Exception:
                date_str = app_item["created_at"][:10]

            btn_label = f"{app_item['job_title']}\n{app_item['organization']} ({date_str})"
            if st.button(
                btn_label,
                key=f"sidebar_app_{app_item['id']}",
                use_container_width=True,
            ):
                try:
                    loaded_package, loaded_job = load_application_data(app_item["id"])
                    st.session_state["active_package"] = loaded_package
                    st.session_state["active_job"] = loaded_job
                    st.session_state["active_app_id"] = app_item["id"]
                    st.rerun()
                except Exception as e:
                    st.error(f"Error loading stored application: {e}")
    else:
        st.info("No applications generated yet.")

# Main area

# Check if there is an active application view loaded
if "active_package" in st.session_state and "active_job" in st.session_state:
    active_package: CompleteApplicationPackage = st.session_state["active_package"]
    active_job: JobListing = st.session_state["active_job"]

    st.markdown("---")
    # Back button to return to search results
    if st.button("Back to Job Search", type="secondary"):
        st.session_state.pop("active_package", None)
        st.session_state.pop("active_job", None)
        st.session_state.pop("active_app_id", None)
        st.rerun()

    active_app_id = st.session_state.get("active_app_id")
    is_archived = False
    if active_app_id:
        try:
            app_details = db.get_full_application(active_app_id)
            if app_details and app_details.get("is_deleted") == 1:
                is_archived = True
        except Exception:
            pass

    if is_archived:
        st.warning("This application is archived. Go to Archived Applications to restore it if needed.")

    st.subheader(f"Tailored Application: {active_job.title} at {active_job.organization}")
    
    # Metadata callout
    with st.expander("View original job details", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            st.markdown(f"**Title:** {active_job.title}")
            st.markdown(f"**Organization:** {active_job.organization}")
            if active_job.position_url:
                st.markdown(f"[View on USAJobs ↗]({active_job.position_url})")
        with c2:
            if active_job.description:
                desc_snippet = active_job.description[:1000] + ("..." if len(active_job.description) > 1000 else "")
                st.markdown(f"**Description Snippet:** {desc_snippet}")
            else:
                st.caption("No description cached.")

    from ui.results_dashboard import render_results_dashboard
    render_results_dashboard(
        package=active_package,
        job_title=active_job.title,
        organization=active_job.organization,
    )

else:
    # Default View: Resume Upload, Search, and listings
    st.markdown("### Step 1: Upload Resume")
    uploaded_file = st.file_uploader(
        "Upload your resume to perform gap analysis, ATS keyword matching, and tailor your materials.",
        type=["pdf", "docx"],
        help="Supports PDF and DOCX files. Text will be parsed automatically.",
    )

    if uploaded_file is not None:
        if "resume_filename" not in st.session_state or st.session_state["resume_filename"] != uploaded_file.name:
            try:
                from services.resume_parser import ResumeParserService
                from crews.resume_profile_crew import ResumeProfileCrew
                
                parser = ResumeParserService()
                file_bytes = uploaded_file.read()
                
                info_placeholder = st.empty()
                def make_retry_callback(placeholder):
                    def on_retry(attempt, wait_time, exception_message=None):
                        placeholder.warning(
                            f"Generation temporarily delayed due to provider rate limits. "
                            f"Retrying (attempt {attempt}/3) in {wait_time:.1f} seconds..."
                        )
                    return on_retry

                with st.spinner("Extracting text from resume..."):
                    extracted_text = parser.parse_resume(uploaded_file.name, file_bytes)
                
                st.session_state["resume_text"] = extracted_text
                st.session_state["resume_filename"] = uploaded_file.name
                
                with st.spinner("Analyzing resume structure and extracting professional profile..."):
                    profile_crew = ResumeProfileCrew(config)
                    profile = profile_crew.run(
                        extracted_text,
                        on_retry=make_retry_callback(info_placeholder)
                    )
                
                info_placeholder.empty()
                st.session_state["resume_profile"] = profile
                db.save_resume_profile(user.id, profile.model_dump_json())
                
                st.success(f"Successfully loaded and extracted structured profile: {uploaded_file.name}")
            except Exception as e:
                err_msg = str(e)
                if "rate limit" in err_msg.lower() or "429" in err_msg:
                    st.error("Resume processing failed: Provider rate limit exceeded after maximum retries. Please wait a minute and try again.")
                else:
                    st.error(f"Failed to process resume: {err_msg}")
                st.session_state.pop("resume_text", None)
                st.session_state.pop("resume_filename", None)
                st.session_state.pop("resume_profile", None)

    # Let's show a neat preview of the structured resume profile if present
    if "resume_profile" in st.session_state:
        profile = st.session_state["resume_profile"]
        with st.expander("View Structured Resume Profile", expanded=False):
            # Extracted Contact Information Grid
            st.markdown("#### Contact Information")
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"**Full Name:** {profile.full_name or 'Not extracted'}")
                st.markdown(f"**Email:** {profile.email or 'Not extracted'}")
            with c2:
                st.markdown(f"**Phone:** {profile.phone or 'Not extracted'}")
                st.markdown(f"**Location:** {profile.location or 'Not extracted'}")
            with c3:
                st.markdown(f"**LinkedIn:** {profile.linkedin_url or 'Not extracted'}")
                st.markdown(f"**GitHub:** {profile.github_url or 'Not extracted'}")
            st.markdown("---")

            if profile.technical_skills:
                st.markdown(f"**Technical Skills:** {', '.join(profile.technical_skills)}")
            
            if profile.experience:
                st.markdown("**Professional Experience:**")
                for exp in profile.experience:
                    st.markdown(f"- **{exp.title}** at *{exp.company}*")
                    st.caption(exp.summary)
                    
            if profile.projects:
                st.markdown("**Key Projects:**")
                for proj in profile.projects:
                    techs = f" ({', '.join(proj.technologies)})" if proj.technologies else ""
                    st.markdown(f"- **{proj.name}**{techs}")
                    st.caption(proj.summary)
                    
            if profile.education:
                st.markdown(f"**Academic Education:** {'; '.join(profile.education)}")
            if profile.achievements:
                st.markdown(f"**Achievements:** {'; '.join(profile.achievements)}")
            if profile.certifications:
                st.markdown(f"**Certifications:** {'; '.join(profile.certifications)}")

    st.markdown("### Step 2: Search Job Listings")
    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        keyword = st.text_input("Job keyword", placeholder="e.g. Data Scientist")
    with col2:
        location = st.text_input("Location (optional)", placeholder="e.g. Washington, DC")
    with col3:
        st.markdown("<br>", unsafe_allow_html=True)
        search_clicked = st.button("Search Jobs", type="primary", use_container_width=True)

    if search_clicked and keyword:
        with st.spinner("Fetching jobs from USAJobs..."):
            listings = usajobs.search_jobs(keyword=keyword, location=location)
        if listings:
            db.save_search(keyword, len(listings), user_id=user.id)
            st.session_state["listings"] = listings
            st.success(f"Found {len(listings)} job listings!")
        else:
            st.warning("No results found. Try a different keyword.")

    if "listings" in st.session_state:
        listings = st.session_state["listings"]
        st.markdown("---")
        st.subheader(f"Job Listings ({len(listings)} results)")
        for i, job in enumerate(listings):
            with st.expander(f"**{job.title}** — {job.organization} | {job.location}"):
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown(f"**Dept:** {job.department}")
                    st.markdown(f"**Grade:** {job.grade_low}–{job.grade_high}")
                    st.markdown(f"**Open:** {job.open_date} → **Close:** {job.close_date}")
                with c2:
                    st.markdown(f"**Salary:** ${job.salary_min}–${job.salary_max} ({job.pay_interval})")
                    st.markdown(f"**Who May Apply:** {job.who_may_apply}")
                    if job.position_url:
                        st.markdown(f"[View on USAJobs ↗]({job.position_url})")
                desc = job.description[:1000] + ("..." if len(job.description) > 1000 else "")
                st.markdown(f"**Description:** {desc}")

                # Analyze Button
                if st.button("Generate Application Materials", key=f"analyze_{i}", type="primary"):
                    if "resume_profile" not in st.session_state:
                        st.warning("Please upload your resume to proceed.")
                    else:
                        try:
                            info_placeholder = st.empty()
                            def make_retry_callback(placeholder):
                                def on_retry(attempt, wait_time, exception_message=None):
                                    placeholder.warning(
                                        f"Generation temporarily delayed due to provider rate limits. "
                                        f"Retrying (attempt {attempt}/3) in {wait_time:.1f} seconds..."
                                    )
                                return on_retry

                            with st.spinner("Analyzing resume and generating tailored application materials..."):
                                from crews.job_search_crew import JobSearchCrew
                                crew = JobSearchCrew(config)
                                package = crew.run(
                                    job,
                                    resume_profile=st.session_state["resume_profile"],
                                    on_retry=make_retry_callback(info_placeholder)
                                )
                            info_placeholder.empty()

                            # Save to SQLite
                            app_id = db.save_application(
                                job_title=job.title,
                                organization=job.organization,
                                job_url=job.position_url,
                                job_description=job.description,
                                user_id=user.id,
                            )
                            db.save_agent_output(app_id, "analysis", package.analysis.model_dump_json())
                            db.save_agent_output(app_id, "resume_package", package.resume_package.model_dump_json())
                            db.save_agent_output(app_id, "outreach_package", package.outreach_package.model_dump_json())
                            
                            # Store new output types
                            if package.resume_analysis:
                                db.save_agent_output(app_id, "resume_analysis", package.resume_analysis.model_dump_json())
                            if package.ats_score:
                                db.save_agent_output(app_id, "ats_score", package.ats_score.model_dump_json())
                            if package.gap_analysis:
                                db.save_agent_output(app_id, "gap_analysis", package.gap_analysis.model_dump_json())

                            st.session_state["active_package"] = package
                            st.session_state["active_job"] = job
                            st.session_state["active_app_id"] = app_id
                            st.success("Tailored application package generated successfully and saved.")
                            st.rerun()
                        except Exception as e:
                            err_msg = str(e)
                            if "rate limit" in err_msg.lower() or "429" in err_msg:
                                st.error("Generation failed: Provider rate limit exceeded after maximum retries. Please wait a minute and try again.")
                            else:
                                st.error(f"Failed to generate materials: {err_msg}")

    # General history view at the bottom of standard search
    st.markdown("---")
    st.subheader("Application History")
    recent_apps = db.get_applications(limit=10, user_id=user.id, include_deleted=False)

    # Render confirmation dialogs/states
    if "confirm_archive_id" in st.session_state:
        conf_id = st.session_state["confirm_archive_id"]
        # Find the app details
        app_to_archive = next((a for a in recent_apps if a["id"] == conf_id), None)
        if app_to_archive:
            st.warning(f"Archive Application: **{app_to_archive['job_title']}** at **{app_to_archive['organization']}**?")
            st.caption("You can restore this application later.")
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("Archive", key="confirm_archive_btn_yes", type="primary"):
                    db.archive_application(conf_id)
                    st.session_state.pop("confirm_archive_id", None)
                    st.success("Application archived.")
                    st.rerun()
            with col_no:
                if st.button("Cancel", key="confirm_archive_btn_no"):
                    st.session_state.pop("confirm_archive_id", None)
                    st.rerun()

    if "confirm_delete_id" in st.session_state:
        conf_id = st.session_state["confirm_delete_id"]
        # Find the app details (can be active or archived)
        all_apps = db.get_applications(limit=100, user_id=user.id, include_deleted=True)
        app_to_delete = next((a for a in all_apps if a["id"] == conf_id), None)
        if app_to_delete:
            st.error(f"Delete Application Permanently: **{app_to_delete['job_title']}** at **{app_to_delete['organization']}**?")
            st.caption("This action cannot be undone.")
            col_yes, col_no = st.columns(2)
            with col_yes:
                if st.button("Delete Permanently", key="confirm_delete_btn_yes", type="primary"):
                    db.delete_application(conf_id)
                    # If this application was currently loaded, clear it
                    if st.session_state.get("active_app_id") == conf_id:
                        st.session_state.pop("active_package", None)
                        st.session_state.pop("active_job", None)
                        st.session_state.pop("active_app_id", None)
                    st.session_state.pop("confirm_delete_id", None)
                    st.success("Application permanently deleted.")
                    st.rerun()
            with col_no:
                if st.button("Cancel", key="confirm_delete_btn_no"):
                    st.session_state.pop("confirm_delete_id", None)
                    st.rerun()

    if recent_apps:
        for app in recent_apps:
            date_str = ""
            try:
                dt = datetime.fromisoformat(app["created_at"])
                date_str = dt.strftime("%b %d, %Y")
            except Exception:
                date_str = app["created_at"][:10]

            col_info, col_open, col_archive, col_delete = st.columns([5, 1, 1, 1])
            with col_info:
                st.markdown(f"**{app['job_title']}** — {app['organization']}<br/><small>Generated: {date_str}</small>", unsafe_allow_html=True)
            with col_open:
                if st.button("Open", key=f"open_active_{app['id']}", use_container_width=True):
                    try:
                        loaded_package, loaded_job = load_application_data(app["id"])
                        st.session_state["active_package"] = loaded_package
                        st.session_state["active_job"] = loaded_job
                        st.session_state["active_app_id"] = app["id"]
                        st.rerun()
                    except Exception as e:
                        st.error(f"Error loading stored application data: {e}")
            with col_archive:
                if st.button("Archive", key=f"archive_active_{app['id']}", use_container_width=True):
                    st.session_state["confirm_archive_id"] = app["id"]
                    st.rerun()
            with col_delete:
                if st.button("Delete", key=f"delete_active_{app['id']}", use_container_width=True):
                    st.session_state["confirm_delete_id"] = app["id"]
                    st.rerun()
    else:
        st.info("No active applications yet. Search for jobs and run the AI workflow!")

    # Archived applications section
    st.markdown("---")
    with st.expander("Archived Applications", expanded=False):
        archived_apps = db.get_applications(limit=20, user_id=user.id, only_deleted=True)
        if archived_apps:
            for app in archived_apps:
                date_str = ""
                try:
                    dt = datetime.fromisoformat(app["created_at"])
                    date_str = dt.strftime("%b %d, %Y")
                except Exception:
                    date_str = app["created_at"][:10]

                col_info, col_open, col_restore, col_delete = st.columns([5, 1, 1, 1])
                with col_info:
                    st.markdown(f"**{app['job_title']}** — {app['organization']}<br/><small>Generated: {date_str}</small>", unsafe_allow_html=True)
                with col_open:
                    if st.button("Open", key=f"open_archived_{app['id']}", use_container_width=True):
                        try:
                            loaded_package, loaded_job = load_application_data(app["id"])
                            st.session_state["active_package"] = loaded_package
                            st.session_state["active_job"] = loaded_job
                            st.session_state["active_app_id"] = app["id"]
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error loading stored application data: {e}")
                with col_restore:
                    if st.button("Restore", key=f"restore_archived_{app['id']}", use_container_width=True):
                        db.restore_application(app["id"])
                        st.success("Application restored.")
                        st.rerun()
                with col_delete:
                    if st.button("Delete", key=f"delete_archived_{app['id']}", use_container_width=True):
                        st.session_state["confirm_delete_id"] = app["id"]
                        st.rerun()
        else:
            st.info("No archived applications.")

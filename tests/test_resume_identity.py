"""
Resume Identity & Application Lifecycle Management Tests
=========================================================
Validates:
- StructuredResumeProfile contact fields schema and defaults.
- Extraction task instruction updates.
- Cover letter personalized header construction in Task.
- Outreach personalization with candidate profile.
- Database auto-migration, soft-delete, restore, and permanent delete.
"""

from __future__ import annotations

import os
import sqlite3
import pytest
from datetime import datetime
from pathlib import Path

from crewai import Agent, Task
from services.llm_service import create_llm
from schemas.resume_profile import StructuredResumeProfile
from schemas.mock_data import generate_mock_resume_profile
from tasks.extraction_tasks import create_profile_extraction_task
from tasks.analysis_tasks import create_resume_task, create_outreach_task, format_profile_to_text
from services.usajobs_service import JobListing
from database.db_manager import DatabaseManager


def test_resume_profile_contact_fields():
    """Test StructuredResumeProfile contact fields defaults and values."""
    # Default values should be None
    profile = StructuredResumeProfile()
    assert profile.full_name is None
    assert profile.email is None
    assert profile.phone is None
    assert profile.linkedin_url is None
    assert profile.github_url is None
    assert profile.location is None

    # Set mock values
    mock_profile = generate_mock_resume_profile()
    assert mock_profile.full_name == "John Doe"
    assert mock_profile.email == "john.doe@example.com"
    assert mock_profile.phone == "1-555-555-5555"
    assert mock_profile.linkedin_url == "linkedin.com/in/johndoe"
    assert mock_profile.github_url == "github.com/johndoe"
    assert mock_profile.location == "Oklahoma City, OK"


def test_format_profile_to_text_includes_identity():
    """Verify that format_profile_to_text includes contact details at the top."""
    profile = generate_mock_resume_profile()
    text = format_profile_to_text(profile)
    
    assert "Full Name:** John Doe" in text
    assert "Email:** john.doe@example.com" in text
    assert "Phone:** 1-555-555-5555" in text
    assert "LinkedIn:** linkedin.com/in/johndoe" in text
    assert "GitHub:** github.com/johndoe" in text
    assert "Location:** Oklahoma City, OK" in text


def test_cover_letter_task_personalization_header():
    """Verify that create_resume_task formats the cover letter header block using actual details."""
    profile = generate_mock_resume_profile()
    job = JobListing(
        position_id="123",
        title="Software Engineer",
        organization="NASA",
        department="Space Science",
        location="Houston, TX",
        salary_min="80000",
        salary_max="120000",
        pay_interval="Per Year",
        grade_low="GS-11",
        grade_high="GS-12",
        position_url="https://nasa.gov",
        open_date="2026-01-01",
        close_date="2026-12-31",
        description="NASA Software Engineering role.",
        qualifications="C++, Git, Space Systems.",
        who_may_apply="US Citizens"
    )

    llm = create_llm(api_key="mock", model_name="llama-3.3-70b-versatile")
    agent = Agent(
        role="Test Agent",
        goal="Test Goal",
        backstory="Test Backstory",
        llm=llm
    )
    analysis_task = Task(
        description="Job analysis",
        expected_output="Analysis",
        agent=agent
    )
    gap_analysis_task = Task(
        description="Gap analysis",
        expected_output="Gaps",
        agent=agent
    )

    task = create_resume_task(
        agent=agent,
        job=job,
        resume_profile=profile,
        analysis_task=analysis_task,
        gap_analysis_task=gap_analysis_task
    )

    current_date = datetime.now().strftime("%B %d, %Y")
    # Verify exact header block formatting is part of the task prompt instructions
    assert "John Doe" in task.description
    assert "john.doe@example.com" in task.description
    assert "1-555-555-5555" in task.description
    assert "linkedin.com/in/johndoe" in task.description
    assert "github.com/johndoe" in task.description
    assert current_date in task.description
    assert "Hiring Manager\nNASA\n\nDear Hiring Manager," in task.description


def test_outreach_task_personalization():
    """Verify that create_outreach_task accepts resume_profile and formats instructions to use details."""
    profile = generate_mock_resume_profile()
    job = JobListing(
        position_id="123",
        title="Software Engineer",
        organization="NASA",
        department="Space Science",
        location="Houston, TX",
        salary_min="80000",
        salary_max="120000",
        pay_interval="Per Year",
        grade_low="GS-11",
        grade_high="GS-12",
        position_url="https://nasa.gov",
        open_date="2026-01-01",
        close_date="2026-12-31",
        description="NASA Software Engineering role.",
        qualifications="C++, Git, Space Systems.",
        who_may_apply="US Citizens"
    )

    llm = create_llm(api_key="mock", model_name="llama-3.3-70b-versatile")
    agent = Agent(
        role="Test Agent",
        goal="Test Goal",
        backstory="Test Backstory",
        llm=llm
    )
    analysis_task = Task(
        description="Job analysis",
        expected_output="Analysis",
        agent=agent
    )
    resume_task = Task(
        description="Resume Task",
        expected_output="Tailored materials",
        agent=agent
    )

    task = create_outreach_task(
        agent=agent,
        job=job,
        resume_profile=profile,
        analysis_task=analysis_task,
        resume_task=resume_task
    )

    assert "John Doe" in task.description
    assert "john.doe@example.com" in task.description
    assert "1-555-555-5555" in task.description


def test_database_lifecycle_and_migration(tmp_path):
    """Verify database auto-migration and Application Lifecycle Actions (Archive, Restore, Delete)."""
    db_file = tmp_path / "test_lifecycle.db"
    db = DatabaseManager(db_file)
    db.initialize()

    # Verify that is_deleted column is automatically added and initialized to 0
    with sqlite3.connect(str(db_file)) as conn:
        cursor = conn.execute("PRAGMA table_info(applications);")
        columns = [row[1] for row in cursor.fetchall()]
        assert "is_deleted" in columns

    # 1. Create a user
    user_id = db.create_user("testuser", "test@example.com", "Test User", "password123")
    
    # 2. Insert two test applications
    app1_id = db.save_application(
        job_title="Software Developer",
        organization="Acme Corp",
        job_url="http://acme.org/jobs/1",
        job_description="Description 1",
        user_id=user_id
    )
    
    app2_id = db.save_application(
        job_title="DevOps Specialist",
        organization="Global Tech",
        job_url="http://global.tech/jobs/2",
        job_description="Description 2",
        user_id=user_id
    )

    # Save mock output
    db.save_agent_output(app1_id, "analysis", '{"role_summary": "Summary"}')

    # Verify by default get_applications returns both (active)
    active_apps = db.get_applications(user_id=user_id)
    assert len(active_apps) == 2
    assert active_apps[0]["is_deleted"] == 0
    assert active_apps[1]["is_deleted"] == 0

    # 3. Archive app 1 (Soft Delete)
    db.archive_application(app1_id)

    # Active applications should now only show app 2
    active_apps = db.get_applications(user_id=user_id, include_deleted=False)
    assert len(active_apps) == 1
    assert active_apps[0]["id"] == app2_id

    # Archived applications only_deleted=True should show app 1
    archived_apps = db.get_applications(user_id=user_id, only_deleted=True)
    assert len(archived_apps) == 1
    assert archived_apps[0]["id"] == app1_id

    # 4. Restore app 1
    db.restore_application(app1_id)

    # Active applications should show both again
    active_apps = db.get_applications(user_id=user_id, include_deleted=False)
    assert len(active_apps) == 2

    # 5. Delete app 1 permanently
    db.delete_application(app1_id)

    # Active applications should show only app 2
    active_apps = db.get_applications(user_id=user_id, include_deleted=True)
    assert len(active_apps) == 1
    assert active_apps[0]["id"] == app2_id

    # Verify that child agent outputs are cascade-deleted
    with sqlite3.connect(str(db_file)) as conn:
        cursor = conn.execute("SELECT COUNT(*) FROM agent_outputs WHERE application_id = ?", (app1_id,))
        count = cursor.fetchone()[0]
        assert count == 0

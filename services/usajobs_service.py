"""
USAJobs API Service
====================
Fetches real federal job listings from the USAJobs Search API.

API Docs: https://developer.usajobs.gov/API-Reference/GET-api-Search

Design Decisions:
- Thin wrapper around the USAJobs REST API.
- Returns normalized Python dicts — callers don't see raw API structure.
- Handles pagination, error logging, and rate-limit awareness.
- Extracts only the fields we need to keep the UI clean.
"""

from dataclasses import dataclass
from typing import Any

import requests
from loguru import logger


@dataclass
class JobListing:
    """Normalized representation of a single USAJobs listing."""

    position_id: str
    title: str
    organization: str
    department: str
    location: str
    salary_min: str
    salary_max: str
    pay_interval: str
    grade_low: str
    grade_high: str
    position_url: str
    open_date: str
    close_date: str
    description: str
    qualifications: str
    who_may_apply: str

    def to_dict(self) -> dict[str, str]:
        """Serialize to plain dict for JSON / Streamlit display."""
        return self.__dict__.copy()


class USAJobsService:
    """Client for the USAJobs Search API."""

    BASE_URL = "https://data.usajobs.gov/api/search"

    def __init__(self, api_key: str, email: str) -> None:
        self.headers = {
            "Authorization-Key": api_key,
            "User-Agent": email,
            "Host": "data.usajobs.gov",
        }

    def search_jobs(
        self,
        keyword: str,
        location: str = "",
        results_per_page: int = 25,
        page: int = 1,
    ) -> list[JobListing]:
        """
        Search USAJobs by keyword and optional location.

        Parameters
        ----------
        keyword : str
            Search term (e.g. "data scientist", "software engineer").
        location : str, optional
            City, state, or zip code filter.
        results_per_page : int
            Number of results (max 500 per API docs).
        page : int
            1-based page number.

        Returns
        -------
        list[JobListing]
            Parsed listings, empty list on error.
        """
        params: dict[str, Any] = {
            "Keyword": keyword,
            "ResultsPerPage": results_per_page,
            "Page": page,
        }
        if location:
            params["LocationName"] = location

        logger.info("USAJobs search — keyword='{}', location='{}'", keyword, location)

        try:
            response = requests.get(
                self.BASE_URL,
                headers=self.headers,
                params=params,
                timeout=30,
            )
            response.raise_for_status()
            data = response.json()

            raw_items = (
                data.get("SearchResult", {})
                .get("SearchResultItems", [])
            )

            listings = [self._parse_item(item) for item in raw_items]
            logger.info("USAJobs returned {} listings", len(listings))
            return listings

        except requests.exceptions.RequestException as exc:
            logger.error("USAJobs API error: {}", exc)
            return []

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_item(item: dict) -> JobListing:
        """Extract relevant fields from a single API result item."""
        pos = item.get("MatchedObjectDescriptor", {})

        # Salary info is nested
        salary = pos.get("PositionRemuneration", [{}])
        salary_obj = salary[0] if salary else {}

        # Location — can be multiple; take the first
        locations = pos.get("PositionLocation", [{}])
        location_str = locations[0].get("LocationName", "Multiple Locations") if locations else "Not specified"

        # Qualifications text
        qual_summary = pos.get("QualificationSummary", "Not provided")

        # Description
        user_area = pos.get("UserArea", {}).get("Details", {})
        description = user_area.get("MajorDuties", "") or pos.get("PositionTitle", "")
        # MajorDuties can be a list in some responses
        if isinstance(description, list):
            description = "\n".join(description)

        who_may_apply = user_area.get("WhoMayApply", {})
        if isinstance(who_may_apply, dict):
            who_may_apply = who_may_apply.get("Name", "Not specified")

        return JobListing(
            position_id=pos.get("PositionID", ""),
            title=pos.get("PositionTitle", "Untitled"),
            organization=pos.get("OrganizationName", "Unknown"),
            department=pos.get("DepartmentName", "Unknown"),
            location=location_str,
            salary_min=salary_obj.get("MinimumRange", "N/A"),
            salary_max=salary_obj.get("MaximumRange", "N/A"),
            pay_interval=salary_obj.get("Description", ""),
            grade_low=pos.get("JobGrade", [{}])[0].get("Code", "N/A") if pos.get("JobGrade") else "N/A",
            grade_high=pos.get("JobGrade", [{}])[-1].get("Code", "N/A") if pos.get("JobGrade") else "N/A",
            position_url=pos.get("PositionURI", ""),
            open_date=pos.get("PublicationStartDate", ""),
            close_date=pos.get("ApplicationCloseDate", ""),
            description=description,
            qualifications=qual_summary,
            who_may_apply=who_may_apply if isinstance(who_may_apply, str) else "Not specified",
        )

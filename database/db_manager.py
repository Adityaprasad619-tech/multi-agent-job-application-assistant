"""
Database Manager
=================
SQLite persistence layer for job search results, application history,
and user management.

Design Decisions:
- SQLite chosen for zero-config, file-based persistence.
- Schema auto-creates on first run via `initialize()`.
- Context manager pattern for safe connection handling.
- All DB operations go through this class — no raw SQL elsewhere.
- Multi-user support: `users` table + `user_id` FK on applications/searches.
- `external_id` on users allows mapping to any auth provider (local, Clerk, etc.).
- FK enforcement enabled via PRAGMA.

Tables:
- users: User accounts (local or synced from external provider).
- job_searches: Search history with keyword + timestamp (per-user).
- applications: Per-job application record (per-user).
- agent_outputs: Raw output from each agent, linked to application.
"""

import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Generator, Optional

from loguru import logger


class DatabaseManager:
    """Thread-safe SQLite manager for multi-user job search data."""

    def __init__(self, db_path: Path) -> None:
        self.db_path = db_path
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    # ------------------------------------------------------------------
    # Connection helpers
    # ------------------------------------------------------------------
    @contextmanager
    def _connect(self) -> Generator[sqlite3.Connection, None, None]:
        """Yield a connection with row_factory, auto-commit on success."""
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ------------------------------------------------------------------
    # Schema
    # ------------------------------------------------------------------
    def initialize(self) -> None:
        """Create tables if they don't exist."""
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    external_id   TEXT    NOT NULL UNIQUE,
                    email         TEXT    NOT NULL UNIQUE,
                    full_name     TEXT    NOT NULL DEFAULT '',
                    password_hash TEXT,
                    provider      TEXT    NOT NULL DEFAULT 'local',
                    resume_profile TEXT,
                    created_at    TEXT    NOT NULL
                );

                CREATE TABLE IF NOT EXISTS job_searches (
                    id            INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id       INTEGER,
                    keyword       TEXT    NOT NULL,
                    results_count INTEGER DEFAULT 0,
                    searched_at   TEXT    NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );

                CREATE TABLE IF NOT EXISTS applications (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id         INTEGER,
                    job_title       TEXT    NOT NULL,
                    organization    TEXT,
                    job_url         TEXT,
                    job_description TEXT,
                    status          TEXT    DEFAULT 'generated',
                    is_deleted      INTEGER DEFAULT 0,
                    created_at      TEXT    NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                );

                CREATE TABLE IF NOT EXISTS agent_outputs (
                    id              INTEGER PRIMARY KEY AUTOINCREMENT,
                    application_id  INTEGER NOT NULL,
                    output_type     TEXT    NOT NULL,
                    content         TEXT    NOT NULL,
                    created_at      TEXT    NOT NULL,
                    FOREIGN KEY (application_id) REFERENCES applications(id)
                );

                CREATE INDEX IF NOT EXISTS idx_applications_user
                    ON applications(user_id);
                CREATE INDEX IF NOT EXISTS idx_searches_user
                    ON job_searches(user_id);
                CREATE INDEX IF NOT EXISTS idx_outputs_application
                    ON agent_outputs(application_id);
                """
            )
            
            # Auto-migration: check if column exists, if not, add it
            try:
                conn.execute("ALTER TABLE users ADD COLUMN resume_profile TEXT;")
                logger.info("Auto-migration: Added resume_profile column to users table.")
            except sqlite3.OperationalError:
                # Column already exists
                pass

            try:
                conn.execute("ALTER TABLE applications ADD COLUMN is_deleted INTEGER DEFAULT 0;")
                logger.info("Auto-migration: Added is_deleted column to applications table.")
            except sqlite3.OperationalError:
                # Column already exists
                pass

        logger.info("Database initialized at {}", self.db_path)

    # ==================================================================
    # USER MANAGEMENT
    # ==================================================================
    def create_user(
        self,
        external_id: str,
        email: str,
        full_name: str,
        password_hash: Optional[str] = None,
        provider: str = "local",
    ) -> int:
        """Create a user and return the internal user id."""
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                """INSERT INTO users
                   (external_id, email, full_name, password_hash, provider, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (external_id, email, full_name, password_hash, provider, now),
            )
            return cursor.lastrowid  # type: ignore[return-value]

    def get_user_by_email(self, email: str) -> Optional[dict[str, Any]]:
        """Look up a user by email. Returns dict or None."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE email = ?", (email,)
            ).fetchone()
            return dict(row) if row else None

    def get_user_by_internal_id(self, user_id: int) -> Optional[dict[str, Any]]:
        """Look up a user by internal DB id."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE id = ?", (user_id,)
            ).fetchone()
            return dict(row) if row else None

    def get_user_by_external(self, external_id: str) -> Optional[dict[str, Any]]:
        """Look up a user by external provider id (clerk_user_id, etc.)."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM users WHERE external_id = ?", (external_id,)
            ).fetchone()
            return dict(row) if row else None

    def save_resume_profile(self, user_id: int, profile_json: str) -> None:
        """Persist structured resume profile JSON for a specific user."""
        with self._connect() as conn:
            conn.execute(
                "UPDATE users SET resume_profile = ? WHERE id = ?",
                (profile_json, user_id),
            )
        logger.info("Saved structured resume profile in SQLite for user_id={}", user_id)

    def get_resume_profile(self, user_id: int) -> Optional[str]:
        """Retrieve stored structured resume profile JSON for a specific user."""
        with self._connect() as conn:
            row = conn.execute(
                "SELECT resume_profile FROM users WHERE id = ?",
                (user_id,),
            ).fetchone()
            return row["resume_profile"] if row else None


    # ==================================================================
    # SEARCH HISTORY (user-scoped)
    # ==================================================================
    def save_search(
        self, keyword: str, results_count: int, user_id: Optional[int] = None
    ) -> int:
        """Record a job search and return its row id."""
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                """INSERT INTO job_searches
                   (user_id, keyword, results_count, searched_at)
                   VALUES (?, ?, ?, ?)""",
                (user_id, keyword, results_count, now),
            )
            return cursor.lastrowid  # type: ignore[return-value]

    def get_search_history(
        self, limit: int = 20, user_id: Optional[int] = None
    ) -> list[dict[str, Any]]:
        """Return recent searches for a user (or all if user_id is None)."""
        with self._connect() as conn:
            if user_id is not None:
                rows = conn.execute(
                    "SELECT * FROM job_searches WHERE user_id = ? ORDER BY searched_at DESC LIMIT ?",
                    (user_id, limit),
                ).fetchall()
            else:
                rows = conn.execute(
                    "SELECT * FROM job_searches ORDER BY searched_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
            return [dict(r) for r in rows]

    # ==================================================================
    # APPLICATIONS (user-scoped)
    # ==================================================================
    def save_application(
        self,
        job_title: str,
        organization: str,
        job_url: str,
        job_description: str,
        user_id: Optional[int] = None,
    ) -> int:
        """Create an application record and return its id."""
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                """INSERT INTO applications
                   (user_id, job_title, organization, job_url, job_description, created_at)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (user_id, job_title, organization, job_url, job_description, now),
            )
            return cursor.lastrowid  # type: ignore[return-value]

    def get_applications(
        self, limit: int = 50, user_id: Optional[int] = None, include_deleted: bool = False, only_deleted: bool = False
    ) -> list[dict[str, Any]]:
        """Return recent applications for a user, optionally filtering by deleted/archived status."""
        with self._connect() as conn:
            query = "SELECT * FROM applications"
            params = []
            conditions = []

            if user_id is not None:
                conditions.append("user_id = ?")
                params.append(user_id)

            if only_deleted:
                conditions.append("is_deleted = 1")
            elif not include_deleted:
                conditions.append("is_deleted = 0")

            if conditions:
                query += " WHERE " + " AND ".join(conditions)

            query += " ORDER BY created_at DESC LIMIT ?"
            params.append(limit)

            rows = conn.execute(query, tuple(params)).fetchall()
            return [dict(r) for r in rows]

    def update_application_status(self, application_id: int, status: str) -> None:
        """Update the status of an application."""
        with self._connect() as conn:
            conn.execute(
                "UPDATE applications SET status = ? WHERE id = ?",
                (status, application_id),
            )

    def archive_application(self, application_id: int) -> None:
        """Soft-delete an application by setting is_deleted = 1."""
        with self._connect() as conn:
            conn.execute(
                "UPDATE applications SET is_deleted = 1 WHERE id = ?",
                (application_id,),
            )
        logger.info("Archived application_id={}", application_id)

    def restore_application(self, application_id: int) -> None:
        """Restore a soft-deleted application by setting is_deleted = 0."""
        with self._connect() as conn:
            conn.execute(
                "UPDATE applications SET is_deleted = 0 WHERE id = ?",
                (application_id,),
            )
        logger.info("Restored application_id={}", application_id)

    def delete_application(self, application_id: int) -> None:
        """Permanently delete an application and its child agent outputs."""
        with self._connect() as conn:
            conn.execute(
                "DELETE FROM agent_outputs WHERE application_id = ?",
                (application_id,),
            )
            conn.execute(
                "DELETE FROM applications WHERE id = ?",
                (application_id,),
            )
        logger.info("Permanently deleted application_id={}", application_id)

    # ==================================================================
    # AGENT OUTPUTS
    # ==================================================================
    def save_agent_output(
        self, application_id: int, output_type: str, content: str
    ) -> int:
        """
        Persist an agent's output.

        Parameters
        ----------
        application_id : int
            FK to the applications table.
        output_type : str
            One of: 'job_analysis', 'resume_recommendations',
            'cover_letter', 'outreach_messages'.
        content : str
            Raw text or JSON string produced by the agent.
        """
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as conn:
            cursor = conn.execute(
                """INSERT INTO agent_outputs
                   (application_id, output_type, content, created_at)
                   VALUES (?, ?, ?, ?)""",
                (application_id, output_type, content, now),
            )
            return cursor.lastrowid  # type: ignore[return-value]

    def get_outputs_for_application(
        self, application_id: int
    ) -> dict[str, str]:
        """Return all agent outputs for an application keyed by output_type."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT output_type, content FROM agent_outputs WHERE application_id = ? ORDER BY created_at",
                (application_id,),
            ).fetchall()
            return {row["output_type"]: row["content"] for row in rows}

    def get_full_application(self, application_id: int) -> dict[str, Any] | None:
        """Return application metadata + all agent outputs combined."""
        with self._connect() as conn:
            app_row = conn.execute(
                "SELECT * FROM applications WHERE id = ?",
                (application_id,),
            ).fetchone()
            if not app_row:
                return None

            outputs = self.get_outputs_for_application(application_id)
            result = dict(app_row)
            result["outputs"] = outputs
            return result

"""
Database Migration Helper
==========================
Handles schema upgrades for existing databases.

Run this script to migrate a pre-auth database to the multi-user schema.

Usage:
    python -m database.migrate

Design Decisions:
- Uses ALTER TABLE to add columns — SQLite does not support full ALTER.
- Safe to run multiple times (idempotent checks).
- Backs up the DB file before migrating.
"""

import shutil
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from loguru import logger


def get_existing_columns(conn: sqlite3.Connection, table: str) -> set[str]:
    """Return the set of column names for a table."""
    cursor = conn.execute(f"PRAGMA table_info({table})")
    return {row[1] for row in cursor.fetchall()}


def migrate(db_path: Path) -> None:
    """
    Apply all pending migrations to the database.

    Safe to run on a fresh DB (tables created by initialize()) or
    on a pre-auth DB that needs the users table and user_id columns.
    """
    if not db_path.exists():
        logger.info("No database file found at {} — nothing to migrate.", db_path)
        return

    # Backup first
    backup_path = db_path.with_suffix(
        f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
    )
    shutil.copy2(db_path, backup_path)
    logger.info("Database backed up to {}", backup_path)

    conn = sqlite3.connect(str(db_path))
    conn.execute("PRAGMA journal_mode=WAL;")

    try:
        # --- Migration 1: Create users table if missing ---
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                external_id   TEXT    NOT NULL UNIQUE,
                email         TEXT    NOT NULL UNIQUE,
                full_name     TEXT    NOT NULL DEFAULT '',
                password_hash TEXT,
                provider      TEXT    NOT NULL DEFAULT 'local',
                created_at    TEXT    NOT NULL
            )
            """
        )
        logger.info("Migration 1: users table ensured.")

        # --- Migration 2: Add user_id to applications ---
        app_cols = get_existing_columns(conn, "applications")
        if "user_id" not in app_cols:
            conn.execute("ALTER TABLE applications ADD COLUMN user_id INTEGER REFERENCES users(id)")
            logger.info("Migration 2: Added user_id to applications.")
        else:
            logger.info("Migration 2: applications.user_id already exists, skipping.")

        # --- Migration 3: Add user_id to job_searches ---
        search_cols = get_existing_columns(conn, "job_searches")
        if "user_id" not in search_cols:
            conn.execute("ALTER TABLE job_searches ADD COLUMN user_id INTEGER REFERENCES users(id)")
            logger.info("Migration 3: Added user_id to job_searches.")
        else:
            logger.info("Migration 3: job_searches.user_id already exists, skipping.")

        # --- Migration 4: Add indexes ---
        conn.execute("CREATE INDEX IF NOT EXISTS idx_applications_user ON applications(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_searches_user ON job_searches(user_id)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_outputs_application ON agent_outputs(application_id)")
        logger.info("Migration 4: Indexes ensured.")

        conn.commit()
        logger.info("All migrations applied successfully.")

    except Exception as exc:
        conn.rollback()
        logger.error("Migration failed: {}", exc)
        raise
    finally:
        conn.close()


if __name__ == "__main__":
    from utils.config import load_config
    from utils.logger import setup_logger

    config = load_config()
    setup_logger(config.log_dir)
    migrate(config.db_path)

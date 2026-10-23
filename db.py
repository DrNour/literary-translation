"""Small SQLite persistence layer for Literary Translation Studio."""

from __future__ import annotations

import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

from seed_data import SEED_TEXTS


DEFAULT_DB_PATH = os.getenv("LITTRANS_DB_PATH", "data/littrans.db")


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _ensure_parent(path: str) -> None:
    parent = Path(path).expanduser().resolve().parent
    parent.mkdir(parents=True, exist_ok=True)


def connect(db_path: str | None = None) -> sqlite3.Connection:
    path = db_path or DEFAULT_DB_PATH
    _ensure_parent(path)
    connection = sqlite3.connect(path, check_same_thread=False)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_db(db_path: str | None = None) -> None:
    with connect(db_path) as connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS learners (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pseudonym TEXT NOT NULL UNIQUE,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS texts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                author TEXT NOT NULL,
                year TEXT,
                language TEXT NOT NULL,
                direction TEXT NOT NULL,
                genre TEXT NOT NULL,
                week INTEGER,
                difficulty TEXT,
                themes TEXT,
                rights TEXT,
                source_url TEXT,
                text TEXT NOT NULL,
                reference_translation TEXT NOT NULL DEFAULT '',
                is_authentic INTEGER NOT NULL DEFAULT 1,
                uploaded_by TEXT,
                created_at TEXT NOT NULL,
                UNIQUE(title, author)
            );

            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                learner_id INTEGER NOT NULL,
                text_id INTEGER NOT NULL,
                workflow_mode TEXT NOT NULL DEFAULT 'Original translation',
                draft TEXT NOT NULL DEFAULT '',
                machine_translation TEXT NOT NULL DEFAULT '',
                post_edit_translation TEXT NOT NULL DEFAULT '',
                final_translation TEXT NOT NULL DEFAULT '',
                commentary TEXT NOT NULL DEFAULT '',
                strategy_tags TEXT NOT NULL DEFAULT '[]',
                status TEXT NOT NULL DEFAULT 'working',
                started_at TEXT NOT NULL,
                locked_at TEXT,
                final_submitted_at TEXT,
                updated_at TEXT NOT NULL,
                reference_translation TEXT NOT NULL DEFAULT '',
                UNIQUE(learner_id, text_id, workflow_mode),
                FOREIGN KEY(learner_id) REFERENCES learners(id) ON DELETE CASCADE,
                FOREIGN KEY(text_id) REFERENCES texts(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS annotations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                submission_id INTEGER NOT NULL,
                span TEXT NOT NULL,
                tag TEXT NOT NULL,
                note TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(submission_id) REFERENCES submissions(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS ai_suggestions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                submission_id INTEGER NOT NULL,
                mode TEXT NOT NULL,
                suggestion TEXT NOT NULL,
                model TEXT NOT NULL,
                used INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL,
                FOREIGN KEY(submission_id) REFERENCES submissions(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS peer_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                submission_id INTEGER NOT NULL,
                reviewer_id INTEGER NOT NULL,
                fidelity_score INTEGER NOT NULL,
                style_score INTEGER NOT NULL,
                cultural_score INTEGER NOT NULL,
                clarity_score INTEGER NOT NULL,
                comment TEXT NOT NULL,
                created_at TEXT NOT NULL,
                UNIQUE(submission_id, reviewer_id),
                FOREIGN KEY(submission_id) REFERENCES submissions(id) ON DELETE CASCADE,
                FOREIGN KEY(reviewer_id) REFERENCES learners(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS teacher_reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                submission_id INTEGER NOT NULL,
                reviewer_label TEXT NOT NULL,
                blinded INTEGER NOT NULL DEFAULT 1,
                fidelity_score INTEGER NOT NULL,
                style_score INTEGER NOT NULL,
                cultural_score INTEGER NOT NULL,
                creativity_score INTEGER NOT NULL,
                commentary TEXT NOT NULL,
                created_at TEXT NOT NULL,
                FOREIGN KEY(submission_id) REFERENCES submissions(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                learner_id INTEGER,
                submission_id INTEGER,
                event_type TEXT NOT NULL,
                payload_json TEXT NOT NULL DEFAULT '{}',
                created_at TEXT NOT NULL,
                FOREIGN KEY(learner_id) REFERENCES learners(id) ON DELETE SET NULL,
                FOREIGN KEY(submission_id) REFERENCES submissions(id) ON DELETE SET NULL
            );
            """
        )
        _migrate_existing_schema(connection)


def _migrate_existing_schema(connection: sqlite3.Connection) -> None:
    """Add the workflow fields while preserving databases created by v1."""

    text_columns = {row[1] for row in connection.execute("PRAGMA table_info(texts)").fetchall()}
    if "reference_translation" not in text_columns:
        connection.execute("ALTER TABLE texts ADD COLUMN reference_translation TEXT NOT NULL DEFAULT ''")

    submission_columns = {row[1] for row in connection.execute("PRAGMA table_info(submissions)").fetchall()}
    if "workflow_mode" not in submission_columns:
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute(
            """
            CREATE TABLE submissions_v2 (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                learner_id INTEGER NOT NULL,
                text_id INTEGER NOT NULL,
                workflow_mode TEXT NOT NULL DEFAULT 'Original translation',
                draft TEXT NOT NULL DEFAULT '',
                machine_translation TEXT NOT NULL DEFAULT '',
                post_edit_translation TEXT NOT NULL DEFAULT '',
                final_translation TEXT NOT NULL DEFAULT '',
                commentary TEXT NOT NULL DEFAULT '',
                strategy_tags TEXT NOT NULL DEFAULT '[]',
                status TEXT NOT NULL DEFAULT 'working',
                started_at TEXT NOT NULL,
                locked_at TEXT,
                final_submitted_at TEXT,
                updated_at TEXT NOT NULL,
                reference_translation TEXT NOT NULL DEFAULT '',
                UNIQUE(learner_id, text_id, workflow_mode),
                FOREIGN KEY(learner_id) REFERENCES learners(id) ON DELETE CASCADE,
                FOREIGN KEY(text_id) REFERENCES texts(id) ON DELETE CASCADE
            )
            """
        )
        connection.execute(
            """
            INSERT INTO submissions_v2
            (id, learner_id, text_id, workflow_mode, draft, final_translation, commentary,
             strategy_tags, status, started_at, locked_at, final_submitted_at, updated_at)
            SELECT id, learner_id, text_id, 'Original translation', draft, final_translation, commentary,
                   strategy_tags, status, started_at, locked_at, final_submitted_at, updated_at
            FROM submissions
            """
        )
        connection.execute("DROP TABLE submissions")
        connection.execute("ALTER TABLE submissions_v2 RENAME TO submissions")
        connection.execute("PRAGMA foreign_keys = ON")
    else:
        for column, definition in {
            "machine_translation": "TEXT NOT NULL DEFAULT ''",
            "post_edit_translation": "TEXT NOT NULL DEFAULT ''",
            "reference_translation": "TEXT NOT NULL DEFAULT ''",
        }.items():
            if column not in submission_columns:
                connection.execute(f"ALTER TABLE submissions ADD COLUMN {column} {definition}")


def seed_database(db_path: str | None = None) -> None:
    """Insert the curated authentic seed catalogue once."""

    with connect(db_path) as connection:
        existing = connection.execute("SELECT COUNT(*) AS count FROM texts").fetchone()["count"]
        if existing:
            return
        for item in SEED_TEXTS:
            connection.execute(
                """
                INSERT OR IGNORE INTO texts
                (title, author, year, language, direction, genre, week, difficulty,
                 themes, rights, source_url, text, reference_translation, is_authentic, uploaded_by, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, ?, ?)
                """,
                (
                    item["title"],
                    item["author"],
                    item.get("year", ""),
                    item["language"],
                    item["direction"],
                    item["genre"],
                    item.get("week"),
                    item.get("difficulty", ""),
                    item.get("themes", ""),
                    item.get("rights", ""),
                    item.get("source_url", ""),
                    item["text"],
                    item.get("reference_translation", ""),
                    "seed-catalogue",
                    now_iso(),
                ),
            )


def _rows(cursor: sqlite3.Cursor) -> list[dict[str, Any]]:
    return [dict(row) for row in cursor.fetchall()]


def get_or_create_learner(pseudonym: str, db_path: str | None = None) -> int:
    clean = pseudonym.strip() or "student-001"
    with connect(db_path) as connection:
        connection.execute(
            "INSERT OR IGNORE INTO learners (pseudonym, created_at) VALUES (?, ?)",
            (clean, now_iso()),
        )
        row = connection.execute("SELECT id FROM learners WHERE pseudonym = ?", (clean,)).fetchone()
        return int(row["id"])


def insert_text(item: dict[str, Any], uploaded_by: str = "instructor", db_path: str | None = None) -> int:
    raw_week = item.get("week")
    if raw_week is None or (isinstance(raw_week, float) and raw_week != raw_week) or str(raw_week).strip() in {"", "None", "nan"}:
        parsed_week = None
    else:
        parsed_week = int(raw_week)
    with connect(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO texts
            (title, author, year, language, direction, genre, week, difficulty,
             themes, rights, source_url, text, reference_translation, is_authentic, uploaded_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(title, author) DO UPDATE SET
              year=excluded.year, language=excluded.language, direction=excluded.direction,
              genre=excluded.genre, week=excluded.week, difficulty=excluded.difficulty,
              themes=excluded.themes, rights=excluded.rights, source_url=excluded.source_url,
              text=excluded.text, reference_translation=excluded.reference_translation,
              uploaded_by=excluded.uploaded_by
            """,
            (
                item["title"].strip(),
                item["author"].strip(),
                str(item.get("year", "")),
                item.get("language", "English"),
                item.get("direction", "English → Arabic"),
                item.get("genre", "Fiction"),
                parsed_week,
                item.get("difficulty", "Intermediate"),
                item.get("themes", ""),
                item.get("rights", "Instructor-provided authentic text."),
                item.get("source_url", ""),
                item["text"].strip(),
                item.get("reference_translation", ""),
                1 if item.get("is_authentic", True) else 0,
                uploaded_by,
                now_iso(),
            ),
        )
        row = connection.execute(
            "SELECT id FROM texts WHERE title = ? AND author = ?",
            (item["title"].strip(), item["author"].strip()),
        ).fetchone()
        return int(row["id"] if row else cursor.lastrowid)


def list_texts(
    *,
    week: int | None = None,
    language: str | None = None,
    genre: str | None = None,
    difficulty: str | None = None,
    search: str = "",
    db_path: str | None = None,
) -> list[dict[str, Any]]:
    clauses: list[str] = []
    params: list[Any] = []
    if week is not None:
        clauses.append("week = ?")
        params.append(week)
    if language and language != "All":
        clauses.append("language = ?")
        params.append(language)
    if genre and genre != "All":
        clauses.append("genre = ?")
        params.append(genre)
    if difficulty and difficulty != "All":
        clauses.append("difficulty = ?")
        params.append(difficulty)
    if search.strip():
        clauses.append("(title LIKE ? OR author LIKE ? OR themes LIKE ? OR text LIKE ?)")
        term = f"%{search.strip()}%"
        params.extend([term, term, term, term])
    query = "SELECT * FROM texts"
    if clauses:
        query += " WHERE " + " AND ".join(clauses)
    query += " ORDER BY COALESCE(week, 99), language, title"
    with connect(db_path) as connection:
        return _rows(connection.execute(query, params))


def get_text(text_id: int, db_path: str | None = None) -> dict[str, Any] | None:
    with connect(db_path) as connection:
        row = connection.execute("SELECT * FROM texts WHERE id = ?", (text_id,)).fetchone()
        return dict(row) if row else None


def get_submission(
    learner_id: int,
    text_id: int,
    db_path: str | None = None,
    workflow_mode: str = "Original translation",
) -> dict[str, Any] | None:
    with connect(db_path) as connection:
        row = connection.execute(
            "SELECT * FROM submissions WHERE learner_id = ? AND text_id = ? AND workflow_mode = ?",
            (learner_id, text_id, workflow_mode),
        ).fetchone()
        return dict(row) if row else None


def save_unlocked_draft(
    learner_id: int,
    text_id: int,
    draft: str,
    db_path: str | None = None,
    workflow_mode: str = "Original translation",
    machine_translation: str = "",
    post_edit_translation: str = "",
) -> int:
    with connect(db_path) as connection:
        existing = connection.execute(
            "SELECT id, locked_at FROM submissions WHERE learner_id = ? AND text_id = ? AND workflow_mode = ?",
            (learner_id, text_id, workflow_mode),
        ).fetchone()
        if existing and existing["locked_at"]:
            return int(existing["id"])
        if existing:
            connection.execute(
                """
                UPDATE submissions
                SET draft = ?, machine_translation = COALESCE(NULLIF(?, ''), machine_translation),
                    post_edit_translation = COALESCE(NULLIF(?, ''), post_edit_translation), updated_at = ?
                WHERE id = ?
                """,
                (draft, machine_translation, post_edit_translation, now_iso(), existing["id"]),
            )
            return int(existing["id"])
        cursor = connection.execute(
            """
            INSERT INTO submissions
            (learner_id, text_id, workflow_mode, draft, machine_translation, post_edit_translation, started_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (learner_id, text_id, workflow_mode, draft, machine_translation, post_edit_translation, now_iso(), now_iso()),
        )
        return int(cursor.lastrowid)


def lock_draft(
    learner_id: int,
    text_id: int,
    draft: str,
    db_path: str | None = None,
    workflow_mode: str = "Original translation",
    machine_translation: str = "",
) -> int:
    submission_id = save_unlocked_draft(
        learner_id,
        text_id,
        draft,
        db_path,
        workflow_mode=workflow_mode,
        machine_translation=machine_translation,
    )
    with connect(db_path) as connection:
        row = connection.execute("SELECT locked_at FROM submissions WHERE id = ?", (submission_id,)).fetchone()
        if row and not row["locked_at"]:
            timestamp = now_iso()
            connection.execute(
                """
                UPDATE submissions
                SET draft = ?, machine_translation = COALESCE(NULLIF(?, ''), machine_translation),
                    status = 'draft_locked', locked_at = ?, updated_at = ?
                WHERE id = ?
                """,
                (draft, machine_translation, timestamp, timestamp, submission_id),
            )
    return submission_id


def save_post_edit(
    submission_id: int,
    post_edit_translation: str,
    commentary: str,
    strategy_tags: Iterable[str],
    *,
    submit: bool = False,
    db_path: str | None = None,
) -> None:
    """Save a student's post-edited version while preserving the MT baseline."""

    tags = json.dumps(list(strategy_tags), ensure_ascii=False)
    timestamp = now_iso()
    with connect(db_path) as connection:
        connection.execute(
            """
            UPDATE submissions
            SET post_edit_translation = ?, final_translation = ?, commentary = ?, strategy_tags = ?,
                status = CASE WHEN ? THEN 'submitted' ELSE status END,
                final_submitted_at = CASE WHEN ? THEN COALESCE(final_submitted_at, ?) ELSE final_submitted_at END,
                updated_at = ?
            WHERE id = ?
            """,
            (
                post_edit_translation,
                post_edit_translation,
                commentary,
                tags,
                1 if submit else 0,
                1 if submit else 0,
                timestamp,
                timestamp,
                submission_id,
            ),
        )


def save_final(
    submission_id: int,
    final_translation: str,
    commentary: str,
    strategy_tags: Iterable[str],
    *,
    submit: bool = False,
    db_path: str | None = None,
) -> None:
    tags = json.dumps(list(strategy_tags), ensure_ascii=False)
    timestamp = now_iso()
    with connect(db_path) as connection:
        if submit:
            connection.execute(
                """
                UPDATE submissions
                SET final_translation = ?, commentary = ?, strategy_tags = ?,
                    status = 'submitted', final_submitted_at = COALESCE(final_submitted_at, ?), updated_at = ?
                WHERE id = ?
                """,
                (final_translation, commentary, tags, timestamp, timestamp, submission_id),
            )
        else:
            connection.execute(
                """
                UPDATE submissions
                SET final_translation = ?, commentary = ?, strategy_tags = ?, updated_at = ?
                WHERE id = ?
                """,
                (final_translation, commentary, tags, timestamp, submission_id),
            )


def add_annotation(submission_id: int, span: str, tag: str, note: str, db_path: str | None = None) -> None:
    with connect(db_path) as connection:
        connection.execute(
            "INSERT INTO annotations (submission_id, span, tag, note, created_at) VALUES (?, ?, ?, ?, ?)",
            (submission_id, span.strip(), tag.strip(), note.strip(), now_iso()),
        )


def list_annotations(submission_id: int, db_path: str | None = None) -> list[dict[str, Any]]:
    with connect(db_path) as connection:
        return _rows(connection.execute("SELECT * FROM annotations WHERE submission_id = ? ORDER BY id", (submission_id,)))


def save_ai_suggestion(
    submission_id: int,
    mode: str,
    suggestion: str,
    model: str,
    db_path: str | None = None,
) -> int:
    with connect(db_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO ai_suggestions (submission_id, mode, suggestion, model, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (submission_id, mode, suggestion, model, now_iso()),
        )
        return int(cursor.lastrowid)


def list_ai_suggestions(submission_id: int, db_path: str | None = None) -> list[dict[str, Any]]:
    with connect(db_path) as connection:
        return _rows(
            connection.execute(
                "SELECT * FROM ai_suggestions WHERE submission_id = ? ORDER BY id",
                (submission_id,),
            )
        )


def mark_ai_suggestion_used(suggestion_id: int, used: bool, db_path: str | None = None) -> None:
    with connect(db_path) as connection:
        connection.execute("UPDATE ai_suggestions SET used = ? WHERE id = ?", (1 if used else 0, suggestion_id))


def log_event(
    event_type: str,
    *,
    learner_id: int | None = None,
    submission_id: int | None = None,
    payload: dict[str, Any] | None = None,
    db_path: str | None = None,
) -> None:
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO events (learner_id, submission_id, event_type, payload_json, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (learner_id, submission_id, event_type, json.dumps(payload or {}, ensure_ascii=False), now_iso()),
        )


def list_events(submission_id: int | None = None, db_path: str | None = None) -> list[dict[str, Any]]:
    with connect(db_path) as connection:
        if submission_id is None:
            return _rows(connection.execute("SELECT * FROM events ORDER BY id"))
        return _rows(connection.execute("SELECT * FROM events WHERE submission_id = ? ORDER BY id", (submission_id,)))


def list_student_submissions(learner_id: int, db_path: str | None = None) -> list[dict[str, Any]]:
    with connect(db_path) as connection:
        return _rows(
            connection.execute(
                """
                SELECT s.*, t.title, t.author, t.week, t.language, t.direction, t.genre, t.text AS source_text,
                       t.reference_translation AS text_reference_translation,
                       l.pseudonym
                FROM submissions s
                JOIN texts t ON t.id = s.text_id
                JOIN learners l ON l.id = s.learner_id
                WHERE s.learner_id = ?
                ORDER BY COALESCE(t.week, 99), s.updated_at DESC
                """,
                (learner_id,),
            )
        )


def list_all_submissions(status: str | None = None, db_path: str | None = None) -> list[dict[str, Any]]:
    with connect(db_path) as connection:
        query = """
            SELECT s.*, t.title, t.author, t.week, t.language, t.direction, t.genre, t.text AS source_text,
                   t.reference_translation AS text_reference_translation,
                   l.pseudonym
            FROM submissions s
            JOIN texts t ON t.id = s.text_id
            JOIN learners l ON l.id = s.learner_id
        """
        params: list[Any] = []
        if status:
            query += " WHERE s.status = ?"
            params.append(status)
        query += " ORDER BY COALESCE(t.week, 99), s.updated_at DESC"
        return _rows(connection.execute(query, params))


def save_peer_review(
    submission_id: int,
    reviewer_id: int,
    scores: dict[str, int],
    comment: str,
    db_path: str | None = None,
) -> None:
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO peer_reviews
            (submission_id, reviewer_id, fidelity_score, style_score, cultural_score, clarity_score, comment, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(submission_id, reviewer_id) DO UPDATE SET
              fidelity_score=excluded.fidelity_score, style_score=excluded.style_score,
              cultural_score=excluded.cultural_score, clarity_score=excluded.clarity_score,
              comment=excluded.comment, created_at=excluded.created_at
            """,
            (
                submission_id,
                reviewer_id,
                scores["fidelity"],
                scores["style"],
                scores["cultural"],
                scores["clarity"],
                comment,
                now_iso(),
            ),
        )


def list_peer_reviews(submission_id: int | None = None, db_path: str | None = None) -> list[dict[str, Any]]:
    with connect(db_path) as connection:
        query = """
            SELECT p.*, l.pseudonym AS reviewer_pseudonym
            FROM peer_reviews p JOIN learners l ON l.id = p.reviewer_id
        """
        params: list[Any] = []
        if submission_id is not None:
            query += " WHERE p.submission_id = ?"
            params.append(submission_id)
        query += " ORDER BY p.created_at DESC"
        return _rows(connection.execute(query, params))


def save_teacher_review(
    submission_id: int,
    reviewer_label: str,
    blinded: bool,
    scores: dict[str, int],
    commentary: str,
    db_path: str | None = None,
) -> None:
    with connect(db_path) as connection:
        connection.execute(
            """
            INSERT INTO teacher_reviews
            (submission_id, reviewer_label, blinded, fidelity_score, style_score, cultural_score,
             creativity_score, commentary, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                submission_id,
                reviewer_label.strip() or "reviewer-1",
                1 if blinded else 0,
                scores["fidelity"],
                scores["style"],
                scores["cultural"],
                scores["creativity"],
                commentary,
                now_iso(),
            ),
        )


def list_teacher_reviews(submission_id: int | None = None, db_path: str | None = None) -> list[dict[str, Any]]:
    with connect(db_path) as connection:
        if submission_id is None:
            return _rows(connection.execute("SELECT * FROM teacher_reviews ORDER BY created_at DESC"))
        return _rows(
            connection.execute(
                "SELECT * FROM teacher_reviews WHERE submission_id = ? ORDER BY created_at DESC",
                (submission_id,),
            )
        )


def export_rows(table: str, db_path: str | None = None) -> list[dict[str, Any]]:
    allowed = {
        "learners",
        "texts",
        "submissions",
        "annotations",
        "ai_suggestions",
        "peer_reviews",
        "teacher_reviews",
        "events",
    }
    if table not in allowed:
        raise ValueError(f"Unsupported export table: {table}")
    with connect(db_path) as connection:
        return _rows(connection.execute(f"SELECT * FROM {table}"))


def count_learners(db_path: str | None = None) -> int:
    with connect(db_path) as connection:
        return int(connection.execute("SELECT COUNT(*) AS count FROM learners").fetchone()["count"])


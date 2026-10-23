"""Research and teaching exports."""

from __future__ import annotations

import io
import json
import zipfile
from typing import Any

import pandas as pd
from docx import Document

from analysis_utils import diff_metrics, elapsed_minutes
from db import export_rows, list_ai_suggestions, list_annotations, list_peer_reviews, list_teacher_reviews


def _csv_bytes(rows: list[dict[str, Any]]) -> bytes:
    frame = pd.DataFrame(rows)
    return frame.to_csv(index=False).encode("utf-8-sig")


def make_submission_docx(submission: dict[str, Any], *, db_path: str | None = None) -> bytes:
    document = Document()
    document.add_heading("Literary Translation Studio — Submission", level=1)
    document.add_paragraph(f"Text: {submission.get('title', '')}")
    document.add_paragraph(f"Author: {submission.get('author', '')}")
    document.add_paragraph(f"Language direction: {submission.get('direction', '')}")
    document.add_paragraph(f"Workflow: {submission.get('workflow_mode', 'Original translation')}")
    document.add_paragraph(f"Research ID: {submission.get('pseudonym', '')}")

    document.add_heading("Source text", level=2)
    document.add_paragraph(submission.get("source_text", ""))
    document.add_heading("Unaided draft", level=2)
    document.add_paragraph(submission.get("draft", ""))
    if submission.get("machine_translation"):
        document.add_heading("Machine-translation draft", level=2)
        document.add_paragraph(submission.get("machine_translation", ""))
    if submission.get("post_edit_translation"):
        document.add_heading("Post-edited translation", level=2)
        document.add_paragraph(submission.get("post_edit_translation", ""))
    if submission.get("text_reference_translation") or submission.get("reference_translation"):
        document.add_heading("Reference translation", level=2)
        document.add_paragraph(
            submission.get("text_reference_translation") or submission.get("reference_translation") or ""
        )
    document.add_heading("Final translation", level=2)
    document.add_paragraph(submission.get("final_translation", ""))
    document.add_heading("Translator's commentary", level=2)
    document.add_paragraph(submission.get("commentary", ""))

    tags = submission.get("strategy_tags", "[]")
    try:
        tags = json.loads(tags) if isinstance(tags, str) else tags
    except json.JSONDecodeError:
        tags = []
    document.add_paragraph("Strategy tags: " + ", ".join(tags))

    baseline = submission.get("machine_translation") or submission.get("draft", "")
    revised = submission.get("post_edit_translation") or submission.get("final_translation", "")
    metrics = diff_metrics(baseline, revised)
    document.add_heading("Revision metrics", level=2)
    for key, value in metrics.items():
        document.add_paragraph(f"{key}: {value}")

    if submission.get("started_at") and submission.get("final_submitted_at"):
        document.add_paragraph(
            f"Elapsed minutes: {elapsed_minutes(submission['started_at'], submission['final_submitted_at'])}"
        )

    annotations = list_annotations(int(submission["id"]), db_path)
    if annotations:
        document.add_heading("Annotations", level=2)
        for annotation in annotations:
            document.add_paragraph(
                f"[{annotation['tag']}] {annotation['span']} — {annotation['note']}"
            )

    suggestions = list_ai_suggestions(int(submission["id"]), db_path)
    if suggestions:
        document.add_heading("AI comparison record", level=2)
        for suggestion in suggestions:
            document.add_paragraph(f"{suggestion['mode']} ({suggestion['model']})")
            document.add_paragraph(suggestion["suggestion"])

    output = io.BytesIO()
    document.save(output)
    return output.getvalue()


def make_research_zip(db_path: str | None = None) -> bytes:
    tables = [
        "learners",
        "texts",
        "submissions",
        "annotations",
        "ai_suggestions",
        "peer_reviews",
        "teacher_reviews",
        "events",
    ]
    dictionary = pd.DataFrame(
        [
            {"table": "learners", "purpose": "Pseudonymous learner identifiers"},
            {"table": "texts", "purpose": "Authentic text catalogue and provenance metadata"},
            {"table": "submissions", "purpose": "Unaided drafts, final translations, commentary, and timestamps"},
            {"table": "annotations", "purpose": "Student annotations and translation-strategy notes"},
            {"table": "ai_suggestions", "purpose": "AI alternatives and student uptake records"},
            {"table": "peer_reviews", "purpose": "Peer assessment ratings and comments"},
            {"table": "teacher_reviews", "purpose": "Teacher or blinded expert ratings"},
            {"table": "events", "purpose": "Interaction and workflow event log"},
        ]
    )
    output = io.BytesIO()
    with zipfile.ZipFile(output, mode="w", compression=zipfile.ZIP_DEFLATED) as archive:
        for table in tables:
            rows = export_rows(table, db_path)
            if table == "learners":
                rows = [
                    {key: value for key, value in row.items() if key not in {"full_name", "student_id"}}
                    for row in rows
                ]
            archive.writestr(f"{table}.csv", _csv_bytes(rows))
        archive.writestr("data_dictionary.csv", dictionary.to_csv(index=False).encode("utf-8-sig"))
        archive.writestr(
            "README.txt",
            "Exports are pseudonymised at the application level; student names and institutional IDs are excluded. Review consent, ethics, and local data-protection requirements before research use.\n",
        )
    return output.getvalue()


def review_summary(submission_id: int, db_path: str | None = None) -> pd.DataFrame:
    rows = []
    for review in list_peer_reviews(submission_id, db_path):
        rows.append(
            {
                "review type": "Peer",
                "reviewer": review.get("reviewer_pseudonym", "anonymous"),
                "fidelity": review["fidelity_score"],
                "style": review["style_score"],
                "cultural": review["cultural_score"],
                "clarity": review["clarity_score"],
                "comment": review["comment"],
            }
        )
    for review in list_teacher_reviews(submission_id, db_path):
        rows.append(
            {
                "review type": "Teacher/expert",
                "reviewer": review["reviewer_label"],
                "fidelity": review["fidelity_score"],
                "style": review["style_score"],
                "cultural": review["cultural_score"],
                "clarity": review["creativity_score"],
                "comment": review["commentary"],
            }
        )
    return pd.DataFrame(rows)


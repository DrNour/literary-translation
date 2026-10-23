"""Literary Translation Studio.

Run with:

    streamlit run app.py

The app is designed around authentic, instructor-curated texts. AI is an
optional comparison layer that becomes available only after the student's
unaided draft is locked.
"""

from __future__ import annotations

import hmac
import io
import json
import os
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
from docx import Document

from ai_service import api_is_configured, generate_machine_translation, generate_suggestions
from analysis_utils import (
    diff_metrics,
    elapsed_minutes,
    icc_two_way_random,
    sentiment_table,
    teacher_average,
    word_count,
)
from db import (
    add_annotation,
    count_learners,
    get_or_create_learner,
    get_submission,
    get_text,
    init_db,
    insert_text,
    list_ai_suggestions,
    list_all_submissions,
    list_annotations,
    list_events,
    list_learners,
    list_peer_reviews,
    list_student_submissions,
    list_teacher_reviews,
    list_texts,
    lock_draft,
    log_event,
    mark_ai_suggestion_used,
    save_final,
    save_post_edit,
    save_peer_review,
    save_teacher_review,
    save_unlocked_draft,
    seed_database,
)
from exports import make_research_zip, make_submission_docx
from seed_data import COURSE_PLAN


DB_PATH = os.getenv("LITTRANS_DB_PATH", "data/littrans.db")
STRATEGY_TAGS = [
    "metaphor",
    "imagery",
    "voice",
    "register",
    "rhythm",
    "rhyme",
    "dialect",
    "dialogue",
    "idiom",
    "wordplay",
    "cultural reference",
    "allusion",
    "domestication",
    "foreignisation",
    "compensation",
    "ethical choice",
]


init_db(DB_PATH)
seed_database(DB_PATH)

st.set_page_config(
    page_title="Literary Translation Studio",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded",
)


def apply_style() -> None:
    st.markdown(
        """
        <style>
        :root {color-scheme: light;}
        .main-title {font-size: 2.3rem; font-weight: 700; color: #102a43; margin-bottom: 0.1rem;}
        .subtitle {color: #243b53; margin-bottom: 1.3rem;}
        .authentic-badge {background: #e8f5e9; color: #1b5e20; padding: 0.25rem 0.55rem; border-radius: 0.4rem; font-size: 0.82rem;}
        .source-card {border-left: 4px solid #2e7d32; padding-left: 0.8rem;}
        [data-testid="stAppViewContainer"] p,
        [data-testid="stAppViewContainer"] label,
        [data-testid="stAppViewContainer"] li,
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] label,
        [data-testid="stSidebar"] li,
        [data-testid="stMarkdownContainer"] {
            color: #172b4d !important;
        }
        [data-testid="stCaptionContainer"] p {
            color: #334e68 !important;
            font-size: 0.9rem;
        }
        [data-testid="stAppViewContainer"] h1,
        [data-testid="stAppViewContainer"] h2,
        [data-testid="stAppViewContainer"] h3,
        [data-testid="stSidebar"] h1,
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            color: #102a43 !important;
        }
        input, textarea {
            color: #102a43 !important;
            background-color: #ffffff !important;
            border-color: #829ab1 !important;
        }
        textarea:disabled, input:disabled {
            color: #172b4d !important;
            -webkit-text-fill-color: #172b4d !important;
            opacity: 1 !important;
        }
        button, [data-baseweb="select"] * {
            color: #102a43 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def _parse_tags(value: str | list[str] | None) -> list[str]:
    if isinstance(value, list):
        return value
    if not value:
        return []
    try:
        parsed = json.loads(value)
        return parsed if isinstance(parsed, list) else []
    except (TypeError, json.JSONDecodeError):
        return []


def _read_uploaded_text(uploaded_file: Any) -> str:
    if uploaded_file is None:
        return ""
    filename = uploaded_file.name.lower()
    payload = uploaded_file.getvalue()
    if filename.endswith(".docx"):
        document = Document(io.BytesIO(payload))
        return "\n\n".join(p.text for p in document.paragraphs if p.text.strip())
    return payload.decode("utf-8-sig", errors="replace")


def _text_label(item: dict[str, Any]) -> str:
    week = f"Week {item['week']}" if item.get("week") else "Unassigned"
    return f"{week} · {item['title']} — {item['author']} ({item['language']})"


def _is_arabic(language: str | None) -> bool:
    return "arab" in (language or "").lower()


def _target_language(direction: str | None) -> str:
    if direction and "→" in direction:
        return direction.split("→", 1)[1].strip()
    return "English"


def _localized_text_area(
    label: str,
    value: str = "",
    *,
    language: str | None = None,
    **kwargs: Any,
) -> str:
    """Render a text area with direction and full-justification for its language."""

    direction = "rtl" if _is_arabic(language) else "ltr"
    alignment = "right" if direction == "rtl" else "left"
    selector_label = label.replace("\\", "\\\\").replace('"', '\\"')
    st.markdown(
        f"""
        <style>
        textarea[aria-label="{selector_label}"] {{
            direction: {direction};
            text-align: {alignment};
            text-justify: inter-word;
            unicode-bidi: plaintext;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    return st.text_area(label, value=value, **kwargs)


def _authenticated_sidebar() -> tuple[str, int | None, bool]:
    st.sidebar.markdown("## Literary Translation Studio")
    st.sidebar.caption("Authentic-text teaching, translation practice, and research analytics")
    role = st.sidebar.radio("Workspace", ["Student", "Instructor", "Research"], key="role")

    if role == "Student":
        full_name = st.sidebar.text_input("Student name", key="student_name")
        student_id = st.sidebar.text_input("Student ID", key="institutional_student_id")
        pseudonym = st.sidebar.text_input(
            "Pseudonymous research ID",
            value="",
            key="pseudonym",
            placeholder="e.g., P001",
            help="Use the unique study ID assigned for this course. It is used in research tables and exports instead of your name or institutional ID.",
        )
        if not full_name.strip() or not student_id.strip() or not pseudonym.strip():
            st.sidebar.warning("Enter your name, Student ID, and assigned research ID to enter the student workspace.")
            return role, None, False
        try:
            learner_id = get_or_create_learner(
                pseudonym,
                DB_PATH,
                full_name=full_name,
                student_id=student_id,
            )
        except ValueError as exc:
            st.sidebar.error(str(exc))
            return role, None, False
        st.sidebar.caption("Your name and Student ID are visible to the instructor; research exports use the pseudonymous ID.")
        return role, learner_id, True

    password = st.sidebar.text_input("Workspace password", type="password", key="workspace_password")
    expected = os.getenv("INSTRUCTOR_PASSWORD", "admin")
    if hmac.compare_digest(password, expected):
        if expected == "admin":
            st.sidebar.warning("Demo password is active. Set INSTRUCTOR_PASSWORD before deployment.")
        return role, None, True
    st.sidebar.info("Enter the configured workspace password to continue.")
    return role, None, False


def _sidebar_navigation(role: str) -> str:
    if role == "Student":
        options = [
            "Course Home",
            "Authentic Text Library",
            "Translation Studio",
            "Post-editing Lab",
            "AI Translation Lab",
            "Peer Review",
            "My Progress",
        ]
    elif role == "Instructor":
        options = [
            "Instructor Dashboard",
            "Authentic Text Library",
            "Text Importer",
            "Assessment",
            "Research & Exports",
        ]
    else:
        options = ["Research Dashboard", "Research & Exports", "Authentic Text Library"]
    return st.sidebar.radio("Navigate", options, key=f"navigation_{role}")


def render_course_home(learner_id: int) -> None:
    st.markdown('<div class="main-title">14-Week Literary Translation Course</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="subtitle">A structured English–Arabic workshop built around authentic literary texts.</div>',
        unsafe_allow_html=True,
    )
    submissions = list_student_submissions(learner_id, DB_PATH)
    completed_weeks = {row.get("week") for row in submissions if row.get("status") == "submitted"}
    progress = len(completed_weeks) / len(COURSE_PLAN)
    col1, col2, col3 = st.columns(3)
    col1.metric("Course progress", f"{len(completed_weeks)}/14 weeks")
    col2.metric("Texts in catalogue", len(list_texts(db_path=DB_PATH)))
    col3.metric("Submitted translations", sum(row.get("status") == "submitted" for row in submissions))
    st.progress(progress)
    st.info(
        "The catalogue prioritises instructor-provided, public-domain, open-licensed, or otherwise authorised texts. "
        "AI-generated passages are not used as the course corpus."
    )

    for week in COURSE_PLAN:
        texts_in_week = list_texts(week=week["week"], db_path=DB_PATH)
        completed = "✅" if week["week"] in completed_weeks else "○"
        with st.expander(f"{completed} Week {week['week']}: {week['title']} · {len(texts_in_week)} authentic texts"):
            left, right = st.columns([2, 1])
            left.markdown(f"**Focus:** {week['focus']}")
            left.markdown(f"**Activities:** {week['activities']}")
            right.markdown(f"**Expected output**\n\n{week['output']}")
            if texts_in_week:
                right.markdown("**Available texts**")
                for item in texts_in_week[:5]:
                    right.caption(f"{item['title']} — {item['author']}")
                if len(texts_in_week) > 5:
                    right.caption(f"+ {len(texts_in_week) - 5} more in the text library")


def _library_filters(prefix: str) -> tuple[int | None, str, str, str, str]:
    all_texts = list_texts(db_path=DB_PATH)
    weeks = ["All"] + [f"Week {week}" for week in range(1, 15)]
    languages = ["All"] + sorted({row["language"] for row in all_texts})
    genres = ["All"] + sorted({row["genre"] for row in all_texts})
    difficulties = ["All"] + sorted({row["difficulty"] for row in all_texts if row.get("difficulty")})
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 2])
    week_value = col1.selectbox("Week", weeks, key=f"week_filter_{prefix}")
    language = col2.selectbox("Language", languages, key=f"language_filter_{prefix}")
    genre = col3.selectbox("Genre", genres, key=f"genre_filter_{prefix}")
    difficulty = col4.selectbox("Difficulty", difficulties, key=f"difficulty_filter_{prefix}")
    search = col5.text_input("Search title, author, theme, or text", key=f"search_filter_{prefix}")
    week = int(week_value.split()[-1]) if week_value != "All" else None
    return week, language, genre, difficulty, search


def render_text_library(role: str, learner_id: int | None = None) -> None:
    st.header("Authentic Text Library")
    st.write(
        "Browse a growing catalogue of authentic literary materials. Each entry retains provenance metadata so that "
        "students work with identifiable authors, editions, genres, and cultural contexts."
    )
    week, language, genre, difficulty, search = _library_filters(role.lower())
    texts = list_texts(
        week=week,
        language=language,
        genre=genre,
        difficulty=difficulty,
        search=search,
        db_path=DB_PATH,
    )
    st.caption(f"{len(texts)} authentic text records match the current filters.")
    if not texts:
        st.warning("No texts match these filters. Instructors can add more through Text Importer.")
        return

    for item in texts:
        with st.expander(f"{_text_label(item)} · {item['genre']}"):
            metadata_left, metadata_right = st.columns([2, 1])
            metadata_left.markdown(
                f"<span class='authentic-badge'>AUTHENTIC SOURCE</span> &nbsp; **Themes:** {item.get('themes') or '—'}",
                unsafe_allow_html=True,
            )
            metadata_left.caption(item.get("rights") or "Rights information not supplied")
            metadata_right.markdown(f"**Difficulty:** {item.get('difficulty') or '—'}")
            metadata_right.markdown(f"**Direction:** {item.get('direction') or '—'}")
            if item.get("source_url"):
                metadata_right.markdown(f"[Open source record]({item['source_url']})")
            _localized_text_area(
                f"Text excerpt ({item['language']})",
                value=item["text"],
                language=item["language"],
                height=170,
                disabled=True,
                key=f"library_text_{role}_{item['id']}",
            )
            if role == "Student" and learner_id is not None:
                if st.button("Open in Translation Studio", key=f"open_text_{item['id']}"):
                    st.session_state["selected_text_id"] = item["id"]
                    st.session_state["navigation_Student"] = "Translation Studio"
                    st.rerun()


def render_annotation_panel(submission_id: int) -> None:
    st.subheader("Close-reading annotations")
    with st.form(f"annotation_form_{submission_id}"):
        span = st.text_input("Word, phrase, or feature", placeholder="e.g., 'summer's lease'")
        tag = st.selectbox("Feature", STRATEGY_TAGS)
        note = st.text_area("Interpretive note", placeholder="What translation problem or effect does this feature create?")
        submitted = st.form_submit_button("Save annotation")
        if submitted:
            if not span.strip() or not note.strip():
                st.warning("Add both a text feature and an interpretive note.")
            else:
                add_annotation(submission_id, span, tag, note, DB_PATH)
                st.success("Annotation saved.")
                st.rerun()
    annotations = list_annotations(submission_id, DB_PATH)
    if annotations:
        frame = pd.DataFrame(annotations)[["span", "tag", "note", "created_at"]]
        st.dataframe(frame, use_container_width=True, hide_index=True)
    else:
        st.caption("No annotations have been saved yet.")


def render_translation_studio(learner_id: int, workflow_mode: str = "Original translation") -> None:
    page_title = "AI Translation Lab" if workflow_mode == "AI-assisted translation" else "Translation Studio"
    st.header(page_title)
    if workflow_mode == "AI-assisted translation":
        st.info(
            "This is an explicit AI-assisted translation activity: write and lock your own draft first, then ask AI for literary alternatives and document how you use them."
        )
    else:
        st.info(
            "This is the original-translation activity: translate the authentic source independently before optional comparison or feedback."
        )
    texts = list_texts(db_path=DB_PATH)
    if not texts:
        st.warning("The text library is empty. Ask an instructor to import authentic texts.")
        return
    labels = [_text_label(item) for item in texts]
    ids = [item["id"] for item in texts]
    selected_id = st.session_state.get("selected_text_id", ids[0])
    index = ids.index(selected_id) if selected_id in ids else 0
    selected_label = st.selectbox("Select an authentic source text", labels, index=index, key="studio_text_select")
    text_item = texts[labels.index(selected_label)]
    text_id = text_item["id"]
    st.session_state["selected_text_id"] = text_id

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Week", text_item.get("week") or "—")
    col2.metric("Genre", text_item["genre"])
    col3.metric("Direction", text_item["direction"])
    col4.metric("Difficulty", text_item.get("difficulty") or "—")
    st.markdown(f"**{text_item['title']}** — {text_item['author']} ({text_item.get('year') or 'date unavailable'})")
    if text_item.get("source_url"):
        st.markdown(f"[View provenance/source record]({text_item['source_url']})")
    _localized_text_area(
        "Authentic source text",
        text_item["text"],
        language=text_item["language"],
        height=250,
        disabled=True,
        key=f"source_{text_id}",
    )

    submission = get_submission(learner_id, text_id, DB_PATH, workflow_mode=workflow_mode)
    locked = bool(submission and submission.get("locked_at"))
    if not locked:
        st.subheader("Stage 1 — Student translation before AI assistance")
        st.info(
            "Complete and save your own translation before using AI comparison tools. Once locked, the first draft is preserved for learning analytics."
        )
        draft_value = submission["draft"] if submission else ""
        draft = _localized_text_area(
            "Your unaided translation",
            value=draft_value,
            language=_target_language(text_item["direction"]),
            height=250,
            key=f"draft_editor_{text_id}",
        )
        save_col, lock_col = st.columns(2)
        if save_col.button("Save working draft", key=f"save_draft_{text_id}"):
            submission_id = save_unlocked_draft(learner_id, text_id, draft, DB_PATH, workflow_mode=workflow_mode)
            log_event("draft_saved", learner_id=learner_id, submission_id=submission_id, payload={"word_count": word_count(draft)}, db_path=DB_PATH)
            st.success("Working draft saved.")
            st.rerun()
        if lock_col.button("Lock unaided draft", type="primary", key=f"lock_draft_{text_id}"):
            if not draft.strip():
                st.warning("Write a draft before locking it.")
            else:
                submission_id = lock_draft(learner_id, text_id, draft, DB_PATH, workflow_mode=workflow_mode)
                log_event("draft_locked", learner_id=learner_id, submission_id=submission_id, payload={"word_count": word_count(draft)}, db_path=DB_PATH)
                st.success("Unaided draft locked. The comparison stage is now available.")
                st.rerun()
        if submission:
            render_annotation_panel(submission["id"])
        return

    submission_id = int(submission["id"])
    st.success("Student draft locked. AI comparison and final-translation tools are now available.")
    draft = submission["draft"]
    _localized_text_area(
        "Locked unaided draft",
        draft,
        language=_target_language(text_item["direction"]),
        height=200,
        disabled=True,
        key=f"locked_draft_{text_id}",
    )

    st.subheader("Stage 2 — AI comparison laboratory")
    st.caption(
        "AI suggestions are comparison materials, not answer keys. Keep a record of what you accept, reject, or adapt."
    )
    if api_is_configured():
        st.success("OpenAI integration is configured with storage disabled for response calls.")
    else:
        st.warning("No OPENAI_API_KEY is configured. Offline demo scaffolds keep the workflow testable.")
    suggestions = list_ai_suggestions(submission_id, DB_PATH)
    if st.button("Generate three comparison alternatives", type="primary", key=f"generate_ai_{submission_id}"):
        with st.spinner("Preparing meaning-, style-, and creativity-focused alternatives..."):
            results = generate_suggestions(text_item["text"], draft, text_item["direction"])
            for result in results:
                suggestion_id = db_save_ai_suggestion(submission_id, result)
                log_event(
                    "ai_suggestions_generated",
                    learner_id=learner_id,
                    submission_id=submission_id,
                    payload={"mode": result["mode"], "model": result["model"], "suggestion_id": suggestion_id},
                    db_path=DB_PATH,
                )
        st.rerun()

    suggestions = list_ai_suggestions(submission_id, DB_PATH)
    for suggestion in suggestions:
        with st.expander(f"{suggestion['mode']} · {suggestion['model']}"):
            _localized_text_area(
                "Comparison suggestion",
                suggestion["suggestion"],
                language=_target_language(text_item["direction"]),
                height=180,
                disabled=True,
                key=f"suggestion_{suggestion['id']}",
            )
            used = st.checkbox(
                "I used an idea from this suggestion",
                value=bool(suggestion["used"]),
                key=f"suggestion_used_{suggestion['id']}",
            )
            if used != bool(suggestion["used"]):
                mark_ai_suggestion_used(suggestion["id"], used, DB_PATH)
                log_event(
                    "ai_suggestion_uptake_changed",
                    learner_id=learner_id,
                    submission_id=submission_id,
                    payload={"suggestion_id": suggestion["id"], "used": used},
                    db_path=DB_PATH,
                )
                st.rerun()

    st.subheader("Stage 3 — Final translation and commentary")
    existing_tags = _parse_tags(submission.get("strategy_tags"))
    final_translation = _localized_text_area(
        "Final translation",
        value=submission.get("final_translation", ""),
        language=_target_language(text_item["direction"]),
        height=250,
        key=f"final_translation_{submission_id}",
    )
    commentary = st.text_area(
        "Translator's commentary",
        value=submission.get("commentary", ""),
        height=180,
        placeholder="Explain your principal choices, alternatives considered, and cultural or stylistic trade-offs.",
        key=f"commentary_{submission_id}",
    )
    strategy_tags = st.multiselect(
        "Strategies represented in this translation",
        STRATEGY_TAGS,
        default=[tag for tag in existing_tags if tag in STRATEGY_TAGS],
        key=f"strategy_tags_{submission_id}",
    )
    save_col, submit_col = st.columns(2)
    if save_col.button("Save final draft", key=f"save_final_{submission_id}"):
        save_final(submission_id, final_translation, commentary, strategy_tags, db_path=DB_PATH)
        log_event("final_saved", learner_id=learner_id, submission_id=submission_id, db_path=DB_PATH)
        st.success("Final draft saved.")
        st.rerun()
    if submit_col.button("Submit final translation", type="primary", key=f"submit_final_{submission_id}"):
        if not final_translation.strip() or not commentary.strip():
            st.warning("Add both a final translation and a translator's commentary before submitting.")
        else:
            save_final(submission_id, final_translation, commentary, strategy_tags, submit=True, db_path=DB_PATH)
            log_event("final_submitted", learner_id=learner_id, submission_id=submission_id, payload={"word_count": word_count(final_translation)}, db_path=DB_PATH)
            st.success("Final translation submitted for review.")
            st.rerun()

    st.subheader("Revision and sentiment comparison")
    metrics = diff_metrics(draft, final_translation)
    metric_cols = st.columns(4)
    metric_cols[0].metric("Draft words", metrics["source_tokens"])
    metric_cols[1].metric("Final words", metrics["revised_tokens"])
    metric_cols[2].metric("Edit rate", metrics["edit_rate"])
    metric_cols[3].metric("Similarity", metrics["similarity"])
    if submission.get("final_submitted_at"):
        st.caption(
            f"Elapsed workflow time: {elapsed_minutes(submission.get('started_at'), submission.get('final_submitted_at'))} minutes"
        )
    versions = {"Source": text_item["text"], "Unaided draft": draft}
    if final_translation.strip():
        versions["Final translation"] = final_translation
    for suggestion in suggestions[:3]:
        versions[f"AI — {suggestion['mode']}"] = suggestion["suggestion"]
    sentiment_frame = sentiment_table(versions)
    st.dataframe(sentiment_frame, use_container_width=True, hide_index=True)
    if not sentiment_frame.empty:
        st.bar_chart(sentiment_frame.set_index("version")["polarity"])
    st.caption("Sentiment and emotion counts are exploratory lexical indicators, not validated literary evaluation.")

    render_annotation_panel(submission_id)
    st.download_button(
        "Download this submission as Word",
        data=make_submission_docx(submission, db_path=DB_PATH),
        file_name=f"literary_translation_submission_{submission_id}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        key=f"download_submission_{submission_id}",
    )


def db_save_ai_suggestion(submission_id: int, result: dict[str, Any]) -> int:
    from db import save_ai_suggestion

    return save_ai_suggestion(submission_id, result["mode"], result["suggestion"], result["model"], DB_PATH)


def render_post_editing_lab(learner_id: int) -> None:
    st.header("Post-editing Lab")
    st.info(
        "This activity gives you a machine-translation baseline and asks you to post-edit it against the authentic source. "
        "Your MT baseline, post-edited version, edit operations, and time-on-task are recorded separately."
    )
    texts = list_texts(db_path=DB_PATH)
    if not texts:
        st.warning("The authentic text library is empty.")
        return
    labels = [_text_label(item) for item in texts]
    ids = [item["id"] for item in texts]
    selected_id = st.session_state.get("postedit_text_id", ids[0])
    index = ids.index(selected_id) if selected_id in ids else 0
    selected_label = st.selectbox("Select an authentic source text", labels, index=index, key="postedit_text_select")
    text_item = texts[labels.index(selected_label)]
    text_id = text_item["id"]
    st.session_state["postedit_text_id"] = text_id
    st.markdown(f"**{text_item['title']}** — {text_item['author']} ({text_item['direction']})")
    _localized_text_area(
        "Authentic source text",
        text_item["text"],
        language=text_item["language"],
        height=220,
        disabled=True,
        key=f"postedit_source_{text_id}",
    )

    workflow_mode = "Post-editing"
    submission = get_submission(learner_id, text_id, DB_PATH, workflow_mode=workflow_mode)
    locked = bool(submission and submission.get("locked_at"))
    if not locked:
        st.subheader("Stage 1 — Obtain and lock the MT baseline")
        st.write("Use an instructor-provided MT output, paste one from an approved system, or generate an optional baseline for demonstration.")
        if st.button("Generate MT baseline with AI", key=f"generate_mt_{text_id}"):
            with st.spinner("Generating a machine-translation baseline..."):
                result = generate_machine_translation(text_item["text"], text_item["direction"])
            submission_id = save_unlocked_draft(
                learner_id,
                text_id,
                result["text"],
                DB_PATH,
                workflow_mode=workflow_mode,
                machine_translation=result["text"],
            )
            log_event(
                "mt_baseline_generated",
                learner_id=learner_id,
                submission_id=submission_id,
                payload={"model": result["model"], "provider": result["provider"]},
                db_path=DB_PATH,
            )
            st.rerun()
        mt_value = submission.get("machine_translation", "") if submission else ""
        mt_draft = _localized_text_area(
            "Machine-translation draft",
            value=mt_value,
            language=_target_language(text_item["direction"]),
            height=220,
            key=f"mt_editor_{text_id}",
            help="Paste the MT output supplied by your instructor or approved translation system.",
        )
        if st.button("Lock MT baseline and begin post-editing", type="primary", key=f"lock_mt_{text_id}"):
            if not mt_draft.strip():
                st.warning("Add or generate a machine-translation draft first.")
            else:
                submission_id = lock_draft(
                    learner_id,
                    text_id,
                    mt_draft,
                    DB_PATH,
                    workflow_mode=workflow_mode,
                    machine_translation=mt_draft,
                )
                log_event(
                    "mt_baseline_locked",
                    learner_id=learner_id,
                    submission_id=submission_id,
                    payload={"word_count": word_count(mt_draft)},
                    db_path=DB_PATH,
                )
                st.success("MT baseline locked. You can now post-edit it.")
                st.rerun()
        return

    submission_id = int(submission["id"])
    mt_draft = submission.get("machine_translation") or submission.get("draft", "")
    st.success("MT baseline locked. The editable post-edit field is now active.")
    _localized_text_area(
        "Locked MT baseline",
        mt_draft,
        language=_target_language(text_item["direction"]),
        height=200,
        disabled=True,
        key=f"locked_mt_{submission_id}",
    )
    post_edit = _localized_text_area(
        "Your post-edited translation",
        value=submission.get("post_edit_translation") or submission.get("final_translation", ""),
        language=_target_language(text_item["direction"]),
        height=240,
        key=f"post_edit_editor_{submission_id}",
    )
    commentary = st.text_area(
        "Post-editing commentary",
        value=submission.get("commentary", ""),
        height=150,
        placeholder="Identify the MT problems you corrected and explain important literary or cultural decisions.",
        key=f"post_edit_commentary_{submission_id}",
    )
    tags = st.multiselect(
        "Post-editing strategies",
        STRATEGY_TAGS,
        default=[tag for tag in _parse_tags(submission.get("strategy_tags")) if tag in STRATEGY_TAGS],
        key=f"post_edit_tags_{submission_id}",
    )
    save_col, submit_col = st.columns(2)
    if save_col.button("Save post-edit", key=f"save_post_edit_{submission_id}"):
        save_post_edit(submission_id, post_edit, commentary, tags, db_path=DB_PATH)
        log_event("post_edit_saved", learner_id=learner_id, submission_id=submission_id, db_path=DB_PATH)
        st.success("Post-edit saved.")
        st.rerun()
    if submit_col.button("Submit post-edited translation", type="primary", key=f"submit_post_edit_{submission_id}"):
        if not post_edit.strip() or not commentary.strip():
            st.warning("Add both a post-edited translation and commentary before submitting.")
        else:
            save_post_edit(submission_id, post_edit, commentary, tags, submit=True, db_path=DB_PATH)
            log_event(
                "post_edit_submitted",
                learner_id=learner_id,
                submission_id=submission_id,
                payload={"word_count": word_count(post_edit)},
                db_path=DB_PATH,
            )
            st.success("Post-edited translation submitted.")
            st.rerun()

    metrics = diff_metrics(mt_draft, post_edit)
    metric_cols = st.columns(5)
    metric_cols[0].metric("MT words", word_count(mt_draft))
    metric_cols[1].metric("Post-edit words", word_count(post_edit))
    metric_cols[2].metric("Insertions", metrics["added_tokens"])
    metric_cols[3].metric("Deletions", metrics["removed_tokens"])
    metric_cols[4].metric("Edit rate", metrics["edit_rate"])
    if submission.get("final_submitted_at"):
        st.caption(f"Post-editing time-on-task: {elapsed_minutes(submission.get('started_at'), submission.get('final_submitted_at'))} minutes")

    versions = {"Source": text_item["text"], "MT baseline": mt_draft, "Post-edited": post_edit}
    if text_item.get("reference_translation"):
        versions["Reference"] = text_item["reference_translation"]
    st.subheader("Source–MT–post-edit comparison")
    st.dataframe(sentiment_table(versions), use_container_width=True, hide_index=True)
    st.caption("Edit rate measures effort-related change; it should not be interpreted as translation quality by itself.")
    render_annotation_panel(submission_id)
    export_submission = dict(submission)
    export_submission["text_reference_translation"] = text_item.get("reference_translation", "")
    st.download_button(
        "Download post-edit record as Word",
        data=make_submission_docx(export_submission, db_path=DB_PATH),
        file_name=f"post_edit_submission_{submission_id}.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        key=f"download_post_edit_{submission_id}",
    )


def render_peer_review(learner_id: int) -> None:
    st.header("Peer Review Workshop")
    submissions = [row for row in list_all_submissions(status="submitted", db_path=DB_PATH) if row["learner_id"] != learner_id]
    if not submissions:
        st.info("Peer-review targets will appear after other students submit final translations.")
        return
    labels = [f"Submission #{row['id']} · Week {row.get('week') or '—'} · {row['title']}" for row in submissions]
    selected = st.selectbox("Select an anonymised submission", labels)
    submission = submissions[labels.index(selected)]
    st.markdown(f"**{submission['title']}** — {submission['author']} ({submission['direction']})")
    _localized_text_area(
        "Source text",
        submission["source_text"],
        language=submission["language"],
        height=160,
        disabled=True,
        key=f"peer_source_{submission['id']}",
    )
    _localized_text_area(
        "Student translation",
        submission["final_translation"],
        language=_target_language(submission["direction"]),
        height=200,
        disabled=True,
        key=f"peer_final_{submission['id']}",
    )
    with st.form(f"peer_review_{submission['id']}_{learner_id}"):
        fidelity = st.slider("Fidelity to meaning", 1, 5, 3)
        style = st.slider("Literary style and voice", 1, 5, 3)
        cultural = st.slider("Cultural and contextual adequacy", 1, 5, 3)
        clarity = st.slider("Clarity and readability", 1, 5, 3)
        comment = st.text_area("Constructive feedback")
        submitted = st.form_submit_button("Submit peer review")
        if submitted:
            save_peer_review(
                submission["id"],
                learner_id,
                {"fidelity": fidelity, "style": style, "cultural": cultural, "clarity": clarity},
                comment,
                DB_PATH,
            )
            log_event("peer_review_submitted", learner_id=learner_id, submission_id=submission["id"], db_path=DB_PATH)
            st.success("Peer review saved.")


def render_my_progress(learner_id: int) -> None:
    st.header("My Progress")
    submissions = list_student_submissions(learner_id, DB_PATH)
    if not submissions:
        st.info("Your work will appear here after you begin a translation.")
        return
    rows = []
    for item in submissions:
        baseline = item.get("machine_translation") or item["draft"]
        outcome = item.get("post_edit_translation") or item.get("final_translation", "")
        metrics = diff_metrics(baseline, outcome)
        events = list_events(item["id"], DB_PATH)
        uptake = sum(1 for event in events if event["event_type"] == "ai_suggestion_uptake_changed" and '"used": true' in event["payload_json"])
        rows.append(
            {
                "week": item.get("week"),
                "text": item["title"],
                "workflow": item.get("workflow_mode", "Original translation"),
                "status": item["status"],
                "direction": item["direction"],
                "draft words": word_count(item["draft"]),
                "final words": word_count(item.get("final_translation", "")),
                "edit rate": metrics["edit_rate"],
                "AI ideas marked used": uptake,
            }
        )
    frame = pd.DataFrame(rows)
    st.dataframe(frame, use_container_width=True, hide_index=True)
    st.bar_chart(frame.groupby("status").size())


def render_instructor_dashboard() -> None:
    st.header("Instructor Dashboard")
    roster = list_learners(DB_PATH)
    if roster:
        st.subheader("Student roster")
        roster_frame = pd.DataFrame(
            [
                {
                    "student name": row.get("full_name") or "Not provided",
                    "student ID": row.get("student_id") or "Not provided",
                    "research ID": row.get("pseudonym") or "—",
                    "submissions": row.get("submission_count", 0),
                    "last activity": row.get("last_activity") or "—",
                }
                for row in roster
            ]
        )
        st.dataframe(roster_frame, use_container_width=True, hide_index=True)

    submissions = list_all_submissions(db_path=DB_PATH)
    all_texts = list_texts(db_path=DB_PATH)
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Learners", count_learners(DB_PATH))
    col2.metric("Authentic texts", len(all_texts))
    col3.metric("Working submissions", sum(row["status"] != "submitted" for row in submissions))
    col4.metric("Final submissions", sum(row["status"] == "submitted" for row in submissions))
    if not submissions:
        st.info("No student submissions are available yet.")
        return
    rows = []
    for item in submissions:
        baseline = item.get("machine_translation") or item["draft"]
        outcome = item.get("post_edit_translation") or item.get("final_translation", "")
        metrics = diff_metrics(baseline, outcome)
        rows.append(
            {
                "submission": item["id"],
                "student name": item.get("full_name") or "Not provided",
                "student ID": item.get("student_id") or "Not provided",
                "research ID": item.get("pseudonym") or "—",
                "week": item.get("week"),
                "text": item["title"],
                "workflow": item.get("workflow_mode", "Original translation"),
                "status": item["status"],
                "direction": item["direction"],
                "edit rate": metrics["edit_rate"],
                "final words": word_count(item.get("final_translation", "")),
            }
        )
    frame = pd.DataFrame(rows)
    st.subheader("Submission overview")
    st.dataframe(frame, use_container_width=True, hide_index=True)
    chart = frame.groupby(["week", "status"], dropna=False).size().unstack(fill_value=0)
    st.subheader("Activity by week")
    st.bar_chart(chart)
    st.caption("Use Assessment for rubric scores, commentary, and blinded expert ratings.")


def render_text_importer() -> None:
    st.header("Authentic Text Importer")
    st.info(
        "Add instructor-provided, public-domain, open-licensed, or otherwise authorised materials. "
        "Record provenance and rights information for every text."
    )
    single_tab, bulk_tab = st.tabs(["Add one text", "Import a CSV catalogue"])
    with single_tab:
        with st.form("single_text_import"):
            title = st.text_input("Title")
            author = st.text_input("Author")
            year = st.text_input("Date or period", placeholder="e.g., 1813 or Abbasid period")
            language = st.selectbox("Source language", ["English", "Arabic", "Other"])
            direction = st.selectbox("Translation direction", ["English → Arabic", "Arabic → English", "Other"])
            genre = st.selectbox("Genre", ["Poetry", "Fiction", "Drama", "Prose", "Other"])
            week = st.number_input("Suggested course week", min_value=1, max_value=14, value=1)
            difficulty = st.selectbox("Difficulty", ["Introductory", "Intermediate", "Advanced"])
            themes = st.text_input("Themes or translation challenges")
            rights = st.text_input("Rights/provenance note", value="Instructor-provided authorised excerpt")
            source_url = st.text_input("Source or bibliographic URL")
            reference_translation = _localized_text_area(
                "Reference translation (optional)",
                language=_target_language(direction),
                height=120,
                help="Use only an authorised reference translation. It is kept separate from the student's work for comparison.",
            )
            text_upload = st.file_uploader("Upload .txt or .docx (optional)", type=["txt", "docx"])
            text_body = _localized_text_area(
                "Authentic text or excerpt",
                language=language,
                height=220,
            )
            submitted = st.form_submit_button("Add to authentic library")
            if submitted:
                content = _read_uploaded_text(text_upload) or text_body
                if not title.strip() or not author.strip() or not content.strip():
                    st.warning("Title, author, and text are required.")
                else:
                    text_id = insert_text(
                        {
                            "title": title,
                            "author": author,
                            "year": year,
                            "language": language,
                            "direction": direction,
                            "genre": genre,
                            "week": week,
                            "difficulty": difficulty,
                            "themes": themes,
                            "rights": rights,
                            "source_url": source_url,
                            "text": content,
                            "reference_translation": reference_translation,
                            "is_authentic": True,
                        },
                        uploaded_by="instructor",
                        db_path=DB_PATH,
                    )
                    st.success(f"Text record #{text_id} added or updated.")
    with bulk_tab:
        st.write("CSV columns: `title, author, year, language, direction, genre, week, difficulty, themes, rights, source_url, text, reference_translation`.")
        csv_upload = st.file_uploader("Upload CSV", type=["csv"], key="bulk_text_csv")
        if csv_upload is not None:
            try:
                frame = pd.read_csv(csv_upload)
                st.dataframe(frame.head(10), use_container_width=True, hide_index=True)
                if st.button("Import authentic catalogue", key="import_catalogue"):
                    required = {"title", "author", "language", "direction", "genre", "text"}
                    missing = required - set(frame.columns)
                    if missing:
                        st.error(f"Missing required columns: {', '.join(sorted(missing))}")
                    else:
                        imported = 0
                        for _, row in frame.iterrows():
                            item = {key: (None if pd.isna(row.get(key)) else row.get(key)) for key in frame.columns}
                            insert_text(item, uploaded_by="bulk-import", db_path=DB_PATH)
                            imported += 1
                        st.success(f"Imported {imported} authentic text records.")
            except Exception as exc:
                st.error(f"Could not read the CSV: {exc}")


def _submission_selector(
    submissions: list[dict[str, Any]],
    key: str,
    *,
    show_identity: bool = False,
) -> dict[str, Any] | None:
    if not submissions:
        return None
    labels = []
    for row in submissions:
        identity = ""
        if show_identity:
            identity = (
                f" · {row.get('full_name') or 'Name not provided'}"
                f" · ID: {row.get('student_id') or 'Not provided'}"
            )
        labels.append(f"Submission #{row['id']} · Week {row.get('week') or '—'} · {row['title']}{identity}")
    selected = st.selectbox("Select submission", labels, key=key)
    return submissions[labels.index(selected)]


def render_assessment() -> None:
    st.header("Assessment and Expert Review")
    submissions = list_all_submissions(status="submitted", db_path=DB_PATH)
    submission = _submission_selector(submissions, "assessment_submission", show_identity=True)
    if submission is None:
        st.info("No submitted translations are available for assessment.")
        return
    st.caption(
        f"Student: {submission.get('full_name') or 'Name not provided'} · "
        f"Student ID: {submission.get('student_id') or 'Not provided'} · "
        f"Research ID: {submission.get('pseudonym') or '—'}"
    )
    st.markdown(
        f"**Source:** {submission['title']} — {submission['author']} ({submission['direction']})  \n"
        f"**Workflow:** {submission.get('workflow_mode', 'Original translation')}"
    )
    _localized_text_area(
        "Source text",
        submission["source_text"],
        language=submission["language"],
        height=160,
        disabled=True,
        key=f"assessment_source_{submission['id']}",
    )
    if submission.get("machine_translation"):
        _localized_text_area(
            "Machine-translation baseline",
            submission["machine_translation"],
            language=_target_language(submission["direction"]),
            height=160,
            disabled=True,
            key=f"assessment_mt_{submission['id']}",
        )
    if submission.get("post_edit_translation"):
        _localized_text_area(
            "Post-edited translation",
            submission["post_edit_translation"],
            language=_target_language(submission["direction"]),
            height=180,
            disabled=True,
            key=f"assessment_postedit_{submission['id']}",
        )
    _localized_text_area(
        "Student final translation",
        submission["final_translation"],
        language=_target_language(submission["direction"]),
        height=200,
        disabled=True,
        key=f"assessment_final_{submission['id']}",
    )
    st.text_area("Translator's commentary", submission["commentary"], height=150, disabled=True, key=f"assessment_commentary_{submission['id']}")
    with st.form(f"teacher_review_form_{submission['id']}"):
        reviewer_label = st.text_input("Reviewer label", value="reviewer-1")
        blinded = st.checkbox("Keep student identity blinded in the research export", value=True)
        fidelity = st.slider("Fidelity to meaning", 1, 5, 3)
        style = st.slider("Literary style and voice", 1, 5, 3)
        cultural = st.slider("Cultural and contextual adequacy", 1, 5, 3)
        creativity = st.slider("Creative and rhetorical effectiveness", 1, 5, 3)
        commentary = st.text_area("Assessment commentary")
        submitted = st.form_submit_button("Save teacher/expert rating")
        if submitted:
            save_teacher_review(
                submission["id"],
                reviewer_label,
                blinded,
                {"fidelity": fidelity, "style": style, "cultural": cultural, "creativity": creativity},
                commentary,
                DB_PATH,
            )
            log_event("teacher_review_saved", submission_id=submission["id"], db_path=DB_PATH)
            st.success("Rating saved.")
    reviews = list_teacher_reviews(submission["id"], DB_PATH)
    if reviews:
        review_frame = pd.DataFrame(reviews)
        review_frame["average"] = review_frame.apply(teacher_average, axis=1)
        st.subheader("Existing teacher/expert ratings")
        st.dataframe(
            review_frame[["reviewer_label", "fidelity_score", "style_score", "cultural_score", "creativity_score", "average", "commentary"]],
            use_container_width=True,
            hide_index=True,
        )
    peer_reviews = list_peer_reviews(submission["id"], DB_PATH)
    if peer_reviews:
        st.subheader("Peer reviews")
        st.dataframe(pd.DataFrame(peer_reviews), use_container_width=True, hide_index=True)


def _research_frame() -> pd.DataFrame:
    submissions = list_all_submissions(db_path=DB_PATH)
    rows = []
    for item in submissions:
        baseline = item.get("machine_translation") or item["draft"]
        outcome = item.get("post_edit_translation") or item.get("final_translation", "")
        metrics = diff_metrics(baseline, outcome)
        reviews = list_teacher_reviews(item["id"], DB_PATH)
        ai_rows = list_ai_suggestions(item["id"], DB_PATH)
        rows.append(
            {
                "submission": item["id"],
                "pseudonym": item["pseudonym"],
                "week": item.get("week"),
                "text": item["title"],
                "workflow": item.get("workflow_mode", "Original translation"),
                "status": item["status"],
                "direction": item["direction"],
                "draft words": word_count(item["draft"]),
                "MT words": word_count(item.get("machine_translation", "")),
                "post-edit words": word_count(item.get("post_edit_translation", "")),
                "final words": word_count(item.get("final_translation", "")),
                "edit rate": metrics["edit_rate"],
                "similarity": metrics["similarity"],
                "elapsed minutes": elapsed_minutes(item.get("started_at"), item.get("final_submitted_at")),
                "AI suggestions": len(ai_rows),
                "AI ideas marked used": sum(row["used"] for row in ai_rows),
                "teacher average": round(sum(teacher_average(review) for review in reviews) / len(reviews), 2) if reviews else None,
            }
        )
    return pd.DataFrame(rows)


def render_research_dashboard() -> None:
    st.header("Research Dashboard")
    st.warning(
        "Analytics are intended to support classroom inquiry. Sentiment indicators are exploratory, and ratings should be interpreted with the study design and ethics approval in view."
    )
    frame = _research_frame()
    if frame.empty:
        st.info("Research tables will populate as students complete translations.")
        return
    completed = frame[frame["status"] == "submitted"]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Records", len(frame))
    col2.metric("Completed", len(completed))
    col3.metric("Mean edit rate", round(frame["edit rate"].mean(), 3))
    col4.metric("AI comparison records", int(frame["AI suggestions"].sum()))
    st.dataframe(frame, use_container_width=True, hide_index=True)
    if "week" in frame.columns:
        st.subheader("Submissions by week")
        st.bar_chart(frame.groupby("week").size())

    submissions = list_all_submissions(status="submitted", db_path=DB_PATH)
    selected = _submission_selector(submissions, "research_submission")
    if selected:
        versions = {"Source": selected["source_text"]}
        if selected.get("machine_translation"):
            versions["MT baseline"] = selected["machine_translation"]
        if selected.get("draft"):
            versions["Student draft"] = selected["draft"]
        if selected.get("post_edit_translation"):
            versions["Post-edited"] = selected["post_edit_translation"]
        if selected.get("final_translation"):
            versions["Final"] = selected["final_translation"]
        if selected.get("text_reference_translation"):
            versions["Reference"] = selected["text_reference_translation"]
        st.subheader("Version comparison")
        st.dataframe(sentiment_table(versions), use_container_width=True, hide_index=True)

    reviews = list_teacher_reviews(db_path=DB_PATH)
    ratings = [
        {"item": review["submission_id"], "rater": review["reviewer_label"], "score": teacher_average(review)}
        for review in reviews
    ]
    icc = icc_two_way_random(ratings)
    st.subheader("Inter-rater reliability")
    st.metric("ICC(2,1) across teacher/expert averages", "Not estimable" if icc is None else icc)
    if icc is None:
        st.caption("At least two raters must score at least two common submissions for this estimate.")


def render_research_exports(*, show_identity: bool = False) -> None:
    st.header("Research Exports")
    st.write(
        "Download pseudonymous tables containing text provenance, drafts, final translations, annotations, AI comparisons, peer reviews, teacher ratings, and event logs."
    )
    st.download_button(
        "Download complete research ZIP",
        data=make_research_zip(DB_PATH),
        file_name="literary_translation_research_export.zip",
        mime="application/zip",
    )
    submissions = list_all_submissions(db_path=DB_PATH)
    selected = _submission_selector(submissions, "export_submission", show_identity=show_identity)
    if selected:
        st.download_button(
            "Download selected submission as Word",
            data=make_submission_docx(selected, db_path=DB_PATH),
            file_name=f"submission_{selected['id']}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            key=f"export_docx_{selected['id']}",
        )
    st.subheader("Data-protection reminders")
    st.markdown(
        "- Use pseudonyms or study IDs rather than student names.\n"
        "- Store only authorised text excerpts and preserve provenance.\n"
        "- Obtain consent and follow institutional ethics and data-protection requirements before research use.\n"
        "- Configure a strong workspace password before deployment."
    )


def main() -> None:
    apply_style()
    role, learner_id, authorized = _authenticated_sidebar()
    if not authorized:
        st.markdown('<div class="main-title">Literary Translation Studio</div>', unsafe_allow_html=True)
        if role == "Student":
            st.info("Enter your Student name and Student ID in the sidebar to enter the student workspace.")
        else:
            st.info("Choose Student mode, or enter the configured instructor/research password.")
        return
    page = _sidebar_navigation(role)
    if role == "Student" and learner_id is not None:
        if page == "Course Home":
            render_course_home(learner_id)
        elif page == "Authentic Text Library":
            render_text_library(role, learner_id)
        elif page == "Translation Studio":
            render_translation_studio(learner_id)
        elif page == "Post-editing Lab":
            render_post_editing_lab(learner_id)
        elif page == "AI Translation Lab":
            render_translation_studio(learner_id, workflow_mode="AI-assisted translation")
        elif page == "Peer Review":
            render_peer_review(learner_id)
        elif page == "My Progress":
            render_my_progress(learner_id)
    elif role == "Instructor":
        if page == "Instructor Dashboard":
            render_instructor_dashboard()
        elif page == "Authentic Text Library":
            render_text_library(role)
        elif page == "Text Importer":
            render_text_importer()
        elif page == "Assessment":
            render_assessment()
        elif page == "Research & Exports":
            render_research_exports(show_identity=True)
    elif role == "Research":
        if page == "Research Dashboard":
            render_research_dashboard()
        elif page == "Research & Exports":
            render_research_exports()
        elif page == "Authentic Text Library":
            render_text_library(role)


if __name__ == "__main__":
    main()


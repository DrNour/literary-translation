from pathlib import Path

from analysis_utils import diff_metrics, icc_two_way_random, sentiment_profile
from db import (
    get_or_create_learner,
    init_db,
    list_texts,
    list_learners,
    lock_draft,
    save_post_edit,
    save_final,
    seed_database,
)


def test_seed_catalogue_contains_many_authentic_texts(tmp_path: Path) -> None:
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    seed_database(db_path)
    texts = list_texts(db_path=db_path)
    assert len(texts) >= 18
    assert all(row["is_authentic"] == 1 for row in texts)


def test_locked_workflow_preserves_draft_and_accepts_final(tmp_path: Path) -> None:
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    seed_database(db_path)
    learner_id = get_or_create_learner("test-student", db_path)
    text_id = list_texts(db_path=db_path)[0]["id"]
    submission_id = lock_draft(learner_id, text_id, "unaided draft", db_path)
    save_final(submission_id, "final translation", "commentary", ["voice"], submit=True, db_path=db_path)
    from db import get_submission

    submission = get_submission(learner_id, text_id, db_path)
    assert submission["draft"] == "unaided draft"
    assert submission["final_translation"] == "final translation"
    assert submission["status"] == "submitted"


def test_instructor_roster_preserves_name_and_student_id(tmp_path: Path) -> None:
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    learner_id = get_or_create_learner(
        "study-p001",
        db_path,
        full_name="Student Example",
        student_id="UAEU-001",
    )
    roster = list_learners(db_path)
    learner = next(row for row in roster if row["id"] == learner_id)
    assert learner["full_name"] == "Student Example"
    assert learner["student_id"] == "UAEU-001"
    assert learner["pseudonym"] == "study-p001"


def test_translation_and_post_editing_are_separate_workflows(tmp_path: Path) -> None:
    db_path = str(tmp_path / "test.db")
    init_db(db_path)
    seed_database(db_path)
    learner_id = get_or_create_learner("workflow-student", db_path)
    text_id = list_texts(db_path=db_path)[0]["id"]
    translation_id = lock_draft(learner_id, text_id, "my translation", db_path, workflow_mode="Original translation")
    post_edit_id = lock_draft(
        learner_id,
        text_id,
        "machine baseline",
        db_path,
        workflow_mode="Post-editing",
        machine_translation="machine baseline",
    )
    assert translation_id != post_edit_id
    save_post_edit(post_edit_id, "post-edited version", "commentary", ["voice"], submit=True, db_path=db_path)
    from db import get_submission

    post_edit = get_submission(learner_id, text_id, db_path, workflow_mode="Post-editing")
    assert post_edit["machine_translation"] == "machine baseline"
    assert post_edit["post_edit_translation"] == "post-edited version"
    assert post_edit["status"] == "submitted"


def test_analytics_are_transparent_and_deterministic() -> None:
    metrics = diff_metrics("one two three", "one different three four")
    assert metrics["added_tokens"] >= 1
    assert metrics["removed_tokens"] >= 1
    profile = sentiment_profile("hope and love, but grief and darkness")
    assert profile["positive_hits"] == 2
    assert profile["negative_hits"] == 2
    ratings = [
        {"item": 1, "rater": "a", "score": 4},
        {"item": 1, "rater": "b", "score": 4},
        {"item": 2, "rater": "a", "score": 2},
        {"item": 2, "rater": "b", "score": 3},
    ]
    assert icc_two_way_random(ratings) is not None


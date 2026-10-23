# Literary Translation Studio

Literary Translation Studio is a Streamlit application for a 14-week English–Arabic literary-translation course. It combines authentic-text teaching, staged translation practice, optional AI comparison, peer review, teacher assessment, and research-ready exports.

## Core principle

The course corpus is built around identifiable authentic literary texts. The included seed catalogue contains public-domain or traditional-source excerpts with provenance metadata. Instructors can add authorised excerpts individually or import a larger catalogue by CSV. AI-generated passages are never treated as the primary course corpus.

## Main capabilities

- 14-week course roadmap with weekly outcomes and authentic-text counts.
- Authentic Text Library with filters for week, language, genre, difficulty, author, themes, and direction.
- Single-text and bulk-CSV import with provenance and rights fields.
- Student close-reading annotations and translation-strategy tags.
- A dedicated Translation Studio for original student translation.
- A dedicated Post-editing Lab with an MT baseline, post-edited version, edit operations, and time-on-task.
- A dedicated AI Translation Lab with locked student drafts and three AI alternatives.
- Optional AI-generated MT baselines or instructor-provided MT outputs.
- Locked unaided first draft before AI comparison.
- Three optional comparison modes: meaning-focused, style-focused, and creative alternative.
- Side-by-side source, draft, AI, and final-translation workflow.
- Revision metrics, elapsed workflow time, edit rate, similarity, and AI-uptake logging.
- Source–MT–post-edit–reference workflow comparisons.
- Translator's commentary and reflective practice.
- Anonymised peer review and instructor/expert rubric assessment.
- Exploratory sentiment and emotion comparison across versions.
- ICC(2,1) estimate when enough blinded expert ratings are available.
- Word export for individual submissions and ZIP/CSV research export for the full dataset.
- Instructor-only student roster with student names and institutional IDs; research views and exports retain only pseudonymous study IDs.
- Offline demo mode when no `OPENAI_API_KEY` is configured.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

The SQLite database is created at `data/littrans.db` on first run. It is ignored by Git so student data are not committed to the repository.

## Configuration

Set these environment variables before deployment:

```bash
export INSTRUCTOR_PASSWORD='use-a-strong-password'
export OPENAI_API_KEY='your-key-if-AI-comparison-is-enabled'
export OPENAI_MODEL='gpt-4o-mini'
```

The AI integration uses `store=False` for Responses API calls. If no key is present, the app displays clearly labelled offline scaffolds and all non-AI course features remain usable.

## Authentic corpus and rights

The seed texts are short excerpts selected from public-domain or traditional works. Instructors remain responsible for checking the applicable jurisdiction, edition, licence, institutional policy, and consent requirements before redistributing or researching any text. For copyrighted works, store only authorised excerpts or bibliographic links.

## Research use

The application is designed to support human-in-the-loop research, but its exploratory sentiment lexicon and classroom analytics are not substitutes for a validated annotation protocol. Instructors can view names and institutional IDs in the protected instructor workspace; research dashboards and ZIP exports exclude those fields and use pseudonymous IDs. Before collecting research data, configure pseudonymous IDs, obtain consent, and follow institutional ethics and data-protection requirements.

## Tests

```bash
pytest -q
```


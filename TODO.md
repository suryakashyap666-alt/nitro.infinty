# TODO: UNIVERSAL EDUCATION & SUBJECT INTELLIGENCE SYSTEM (Nitro Infinity AI)

## Plan steps
1. Confirm current universal education architecture (9-subject taxonomy) and bot gating behavior in `backend/brain/core.py`.
2. Replace/enrich `backend/education/subjects.py` to include the requested complete subject taxonomy via alias/keywords expansion while keeping stable 9 subject_ids.
3. Upgrade `backend/brain/learning.py` to do adaptive learning per `subject_id` using weak/strong, learning speed proxy, and learning style; ensure quiz/worksheet correctness updates are wired.
4. Implement missing helper methods referenced by core (`_teach_subject/_quiz_subject/_worksheet_subject/_studyplan_subject`) if any are missing or incomplete; ensure quiz/worksheet generation returns correctness metadata needed for updates.
5. Wire quiz/worksheet correctness to adaptive updates: ensure `#answer` properly calls `update_subject_from_quiz` / `update_subject_from_worksheet` with correct `subject_id`.
6. Ensure MULTILINGUAL EDUCATION support hooks: add language-aware text markers where needed, without breaking existing multilingual system.
7. Smoke test:
   - MAIN: `#learn <subject>`, `#quiz <subject>`, `#worksheet <subject>`, `#studyplan <subject> 7`, then `#answer correct:true ...`.
   - Bot gating: same commands on a bot with educationEnabled disabled.

## Progress
- [x] Investigated existing files: `backend/education/subjects.py`, `backend/brain/learning.py`, `backend/brain/education_subjects_engine.py`, `backend/brain/core.py`.
- [ ] Update `backend/education/subjects.py` to match the requested subject list using alias/keywords.
- [ ] Upgrade `backend/brain/learning.py` adaptive logic per subject_id.
- [ ] Ensure helper method wiring for quiz/worksheet correctness updates.
- [ ] Run smoke tests.


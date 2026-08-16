from __future__ import annotations

import random
from typing import Any, Dict, List, Tuple

try:
    from legacy.education.subjects import LEVELS, SUBJECTS, Subject, detect_subject_id
except (ImportError, ValueError):
    try:
        from education.subjects import LEVELS, SUBJECTS, Subject, detect_subject_id
    except (ImportError, ValueError):
        LEVELS = {}
        SUBJECTS = {}

        def detect_subject_id(message: str, fallback: str = "mathematics") -> str:
            return fallback


def _style_prefix(learning_style: str) -> str:
    if learning_style == "steps":
        return "Step-by-step"
    if learning_style == "probe":
        return "Concept-first"
    return "Adaptive"


class EducationSubjectsEngine:
    """Pure helper that generates teach/quiz/worksheet/studyplan content."""

    def teach(self, *, subject_id: str, learning_style: str, difficulty: str) -> str:
        subj = SUBJECTS.get(subject_id)
        if not subj:
            return f"I can teach a bit about {subject_id}. Tell me your grade level and I’ll tailor it."

        prefix = _style_prefix(learning_style)
        topic_list = ", ".join(list(subj.subtopics)[:3])

        return (
            f"[{prefix} Teaching • {subj.level}] {subj.name} (difficulty: {difficulty})\n"
            "\n"
            "Micro-lesson:\n"
            f"- Today we’ll focus on: {topic_list}.\n"
            "- I’ll explain the idea in a simple way, then show one example.\n"
            "- If you struggle, I’ll switch to the exact step you missed.\n"
            "\n"
            "To practice next, say: #quiz "
            f"{subj.id}\n"
        )

    def quiz(self, *, subject_id: str, learning_style: str, difficulty: str) -> Dict[str, Any]:
        subj = SUBJECTS.get(subject_id)
        if not subj:
            q = "What topic are you trying to practice?"
            return {
                "prompt": q,
                "subject_id": subject_id,
                "answer_key": None,
                "style": learning_style,
                "difficulty": difficulty,
            }

        subtopics = list(subj.subtopics)
        chosen_sub = random.choice(subtopics) if subtopics else subj.id

        if learning_style == "probe":
            q = (
                f"Concept check: In {subj.name}, what does '{chosen_sub}' mainly help you understand? (Choose one)\n"
                f"A) Basics of {chosen_sub}\nB) Unrelated facts\nC) Memory tricks only"
            )
            answer = "A"
        elif learning_style == "steps":
            q = (
                f"Steps practice: Solve this quickly for {subj.name} → '{chosen_sub}'. Choose the next step.\n"
                "A) Identify the key idea\nB) Skip straight to final\nC) Add random details"
            )
            answer = "A"
        else:
            q = (
                f"Quick quiz ({difficulty}) in {subj.name}: Which option is correct about '{chosen_sub}'?\n"
                "A) It is a relevant sub-skill\nB) It is not related\nC) It changes every time"
            )
            answer = "A"

        return {
            "prompt": q,
            "subject_id": subj.id,
            "answer_key": answer,
            "style": learning_style,
            "difficulty": difficulty,
        }

    def worksheet(self, *, subject_id: str, learning_style: str, difficulty: str) -> Dict[str, Any]:
        subj = SUBJECTS.get(subject_id)
        if not subj:
            return {
                "prompt": "Worksheet unavailable. Tell me a subject.",
                "subject_id": subject_id,
                "answer_key": [],
            }

        sts = list(subj.subtopics)[:5] if subj.subtopics else [subj.id]
        items: List[Tuple[str, str]] = []
        for i, st in enumerate(sts):
            items.append(
                (
                    f"Q{i+1}. For {subj.name}, '{st}': which is the best description?\nA) Relevant skill\nB) Unrelated\nC) Random\n",
                    "A",
                )
            )

        full = "Worksheet\n" + "\n".join([q for q, _ in items])
        return {
            "prompt": full,
            "subject_id": subj.id,
            "answer_key": [a for _, a in items],
            "style": learning_style,
            "difficulty": difficulty,
        }

    def studyplan(self, *, subject_id: str, days: int, learning_style: str) -> str:
        subj = SUBJECTS.get(subject_id)
        if not subj:
            return f"Studyplan: tell me the subject id for day {days}."

        days = max(1, min(int(days), 60))
        subtopics = list(subj.subtopics)
        chunks = [subtopics[i : i + 3] for i in range(0, min(len(subtopics), days * 3), 3)]

        lines = [f"Study Plan ({days} days) • {subj.name}", f"Style: {_style_prefix(learning_style)}", ""]
        for d in range(1, days + 1):
            focus = chunks[d - 1] if d - 1 < len(chunks) else subtopics[:3]
            focus_str = ", ".join(focus) if isinstance(focus, list) else str(focus)
            lines.append(f"Day {d}: Learn → #learn {subj.id} ({focus_str})")
            lines.append(f"        Practice → #quiz {subj.id}")
            if d % 3 == 0:
                lines.append(f"        Worksheet → #worksheet {subj.id}")
        return "\n".join(lines) + "\n"
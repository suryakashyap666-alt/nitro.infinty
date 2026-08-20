from __future__ import annotations

import random
from typing import Any, Dict, List

try:
    from legacy.education.subjects import SUBJECTS
except (ImportError, ValueError):
    SUBJECTS = {}


class EducationSubjectsEngine:
    """Universal curriculum, science, history, and education module."""

    def teach(self, subject_id: str, learning_style: str = "adaptive", difficulty: str = "medium") -> str:
        subj = SUBJECTS.get(subject_id)
        name = subj.name if subj else subject_id.title()
        topics = ", ".join(list(subj.subtopics)[:3]) if (subj and subj.subtopics) else "Core Concepts"

        return (
            f"### 📚 Nitro Lesson: {name} ({difficulty.capitalize()})\n\n"
            f"**Key Focus Areas:** {topics}\n\n"
            "**1. Core Mechanism:** Break the concept into fundamental principles rather than memorizing formulas.\n"
            "**2. Practical Application:** Observe how this rule behaves under standard and edge conditions.\n\n"
            "Ask any question or type `#quiz` to test your recall."
        )

    def quiz(self, subject_id: str, learning_style: str = "adaptive", difficulty: str = "medium") -> Dict[str, Any]:
        subj = SUBJECTS.get(subject_id)
        name = subj.name if subj else subject_id.title()
        return {
            "prompt": f"Quick Check ({difficulty.title()}) in {name}:\n\nExplain the primary rule of this topic and give a 1-sentence example.",
            "subject_id": subject_id,
            "difficulty": difficulty,
        }

    def studyplan(self, subject_id: str, days: int = 7) -> str:
        subj = SUBJECTS.get(subject_id)
        name = subj.name if subj else subject_id.title()
        lines = [f"### 📅 {days}-Day Study Plan: {name}\n"]
        for d in range(1, min(days + 1, 15)):
            lines.append(f"• **Day {d}:** Concept Mastery & Problem Verification")
        return "\n".join(lines)
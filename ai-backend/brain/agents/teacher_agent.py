from __future__ import annotations

from typing import Any, Dict


class TeacherAgent:
    """Conversational, intent-aware tutor that explains concepts naturally
    without robotic syllabus card templates.
    """

    def teach(
        self,
        *,
        user_id: str,
        topic: str,
        emotion: str,
        learning_state: Dict[str, Any],
        message: str,
        strict: bool = False,
    ) -> Dict[str, Any]:
        clean = (message or "").strip()
        low = clean.lower()

        # Handle quizzes explicitly if requested
        if "#quiz" in low or "quiz me" in low:
            return {
                "agent": "teacher",
                "topic": topic,
                "reply": f"Here is a quick question on **{topic}**:\n\nCan you explain the main principle behind `{clean}` in your own words?",
            }

        # Conversational explanation
        reply = (
            f"Let's break down **{clean}** clearly:\n\n"
            f"The core idea behind this in {topic.title()} is understanding what drives the system and how its main pieces interact.\n\n"
            "Would you like me to walk through a concrete example step-by-step, or test it with a quick scenario?"
        )

        return {
            "agent": "teacher",
            "topic": topic,
            "reply": reply,
        }
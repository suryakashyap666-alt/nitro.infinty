from __future__ import annotations

from typing import Any, Dict, Tuple


class ExamEngine:
    """Mock test and examination generation engine."""

    def handle_question(self, message: str) -> Tuple[str, Dict[str, Any]]:
        reply = (
            "### 🎯 Exam Checkpoint\n\n"
            "**Question:** Solve for $x$ in the equation $2x^2 - 8x + 6 = 0$.\n\n"
            "*(Reply with your step-by-step working to verify)*"
        )
        return reply, {"topic": "algebra", "style": "IIT/CBSE"}
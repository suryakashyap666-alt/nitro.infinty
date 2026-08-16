from __future__ import annotations

import re
from typing import Dict, List


class TopicDetector:
    """Rule-based topic detector."""

    def __init__(self) -> None:
        self.rules: Dict[str, List[str]] = {
            "algebra": [
                r"\balgebra\b",
                r"quadratic",
                r"equation",
                r"factor",
                r"polynomial",
                r"x\^\d+",
                r"solve for",
            ],
            "geometry": [
                r"\bgeometry\b",
                r"triangle",
                r"circle",
                r"radius",
                r"area",
                r"perimeter",
                r"angle",
                r"similar",
            ],
            "calculus": [
                r"\bcalculus\b",
                r"derivative",
                r"integral",
                r"limit",
                r"d/dx",
                r"\u222b",
                r"\u2202",
            ],
            "coding": [
                r"\bcode\b",
                r"python",
                r"javascript",
                r"react",
                r"fastapi",
                r"bug",
                r"compile",
                r"function",
                r"class",
                r"stack trace",
            ],
            "general": [
                r"\bhello\b",
                r"help",
                r"how to",
                r"what is",
                r"explain",
                r"i need",
                r"teach",
            ],
        }

    def detect_topic(self, message: str) -> str:
        msg = (message or "").lower().strip()
        if not msg:
            return "general"

        best_topic = "general"
        best_score = -1

        for topic, patterns in self.rules.items():
            score = 0
            for p in patterns:
                if re.search(p, msg):
                    score += 1
            if score > best_score:
                best_score = score
                best_topic = topic

        if best_topic != "general" and best_score <= 0:
            best_topic = "general"

        # Command-aware override
        if any(k in msg for k in ["#code", "#explain", "#debug", "#review", "#teach"]):
            return "coding"
        if "#solve" in msg:
            return "algebra"
        if "#question" in msg or "#answer" in msg:
            return "general"

        return best_topic


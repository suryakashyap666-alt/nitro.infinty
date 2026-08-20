from __future__ import annotations

import re
from typing import Any, Dict


class RiskAnalyzer:
    """Safety and ethical guardrails analyzer."""

    def analyze(self, message: str, user_id: str = "") -> Dict[str, Any]:
        low = (message or "").lower()
        blocked_terms = ["how to make a bomb", "mass shooting", "suicide", "child sexual", "credit card fraud"]
        for term in blocked_terms:
            if term in low:
                return {
                    "blocked": True,
                    "category": "safety",
                    "reply": "I cannot fulfill this request because it violates safety and ethical policies.",
                }
        return {"blocked": False, "category": "", "reply": ""}
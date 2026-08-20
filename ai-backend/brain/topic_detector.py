from __future__ import annotations

import re


class TopicDetector:
    """Intent and domain classification across Nitro's 16 capabilities."""

    def detect_topic(self, message: str) -> str:
        low = (message or "").lower().strip()
        if any(k in low for k in ["solve", "derivative", "integral", "equation", "math", "+", "=", "*"]):
            return "math"
        if any(k in low for k in ["code", "python", "javascript", "react", "fastapi", "bug"]):
            return "coding"
        if any(k in low for k in ["image", "picture", "draw", "render", "art"]):
            return "image"
        if any(k in low for k in ["quiz", "exam", "lesson", "teach"]):
            return "education"
        return "general"
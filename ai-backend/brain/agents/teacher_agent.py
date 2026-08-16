from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class TeacherPlan:
    style: str
    steps: List[str]
    next_prompt: str


class TeacherAgent:
    """Intelligent, intent-aware educational assistant.

    Adapts dynamically to the user's actual question, topic, and intent
    rather than forcing a rigid language/grammar critique.
    """

    def __init__(self) -> None:
        pass

    def _is_explicit_curriculum_request(self, text: str) -> bool:
        """Checks if the user explicitly requested a structured syllabus or worksheet."""
        low = (text or "").lower().strip()
        triggers = [
            "#learn",
            "#quiz",
            "#worksheet",
            "#studyplan",
            "give me a quiz",
            "give me a worksheet",
            "create a study plan",
            "test my knowledge",
            "generate questions for",
        ]
        return any(t in low for t in triggers)

    def _is_greeting_or_casual(self, text: str) -> bool:
        low = (text or "").lower().strip()
        greetings = ["hi", "hello", "hey", "good morning", "good evening", "how are you", "who are you", "what's up", "namaste"]
        return low in greetings or any(low.startswith(g + " ") for g in greetings)

    def _coaching_line(self, emotion: str) -> str:
        if emotion == "sad":
            return "Take your time—learning new concepts is a step-by-step journey."
        if emotion == "angry":
            return "Let’s break this down simply and resolve any confusion."
        if emotion == "happy":
            return "Great energy! Let’s explore this topic further."
        return ""

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
        """Dynamically generates educational responses based on user context."""
        clean_msg = (message or "").strip()
        low_msg = clean_msg.lower()

        # 1. Handle Greetings & Casual Interaction
        if self._is_greeting_or_casual(clean_msg):
            reply = (
                "Hello! I am your AI Learning Mentor. I'm here to help you understand complex concepts, "
                "solve problems across mathematics, science, programming, history, and more, or guide you through "
                "step-by-step topics. What would you like to explore or learn today?"
            )
            return {
                "agent": "teacher",
                "topic": "general",
                "reply": reply,
                "plan": {"style": "Conversational Mentor", "steps": [], "next_prompt": "Ask any question to begin."},
            }

        # 2. Handle Explicit Structured Study Requests (#quiz, #worksheet, #studyplan)
        if self._is_explicit_curriculum_request(clean_msg):
            return self._build_structured_lesson(topic=topic, emotion=emotion, message=clean_msg, strict=strict)

        # 3. Dynamic Knowledge / Concept Explanation
        # Detect the subject focus from the user query
        focus = topic if topic and topic != "general" else self._extract_subject_from_query(clean_msg)
        coaching = self._coaching_line(emotion)

        explanation_body = self._generate_concept_breakdown(clean_msg, focus)

        parts = []
        if coaching:
            parts.append(f"*{coaching}*\n")
        parts.append(explanation_body)

        if not strict:
            parts.append(
                f"\n---\n💡 *Tip:* Ask for examples, a deeper dive into any specific part, or type `#quiz {focus}` when you want to test your understanding."
            )

        reply_text = "\n".join(parts).strip()

        return {
            "agent": "teacher",
            "topic": focus,
            "reply": reply_text,
            "plan": {
                "style": "Adaptive Explanation",
                "steps": ["Identify Core Concept", "Explain Mechanism/Logic", "Provide Illustrative Example"],
                "next_prompt": "Follow up with specific questions or practice.",
            },
        }

    def _extract_subject_from_query(self, message: str) -> str:
        low = message.lower()
        if any(k in low for k in ["python", "code", "programming", "javascript", "react", "algorithm", "function"]):
            return "Computer Science"
        if any(k in low for k in ["math", "algebra", "calculus", "geometry", "equation", "derivative", "integral"]):
            return "Mathematics"
        if any(k in low for k in ["physics", "chemistry", "biology", "science", "cell", "gravity", "energy"]):
            return "Science"
        if any(k in low for k in ["history", "war", "civilization", "empire", "revolution"]):
            return "History"
        if any(k in low for k in ["business", "finance", "economy", "market", "accounting"]):
            return "Commerce & Economics"
        return "General Knowledge"

    def _generate_concept_breakdown(self, query: str, subject: str) -> str:
        """Produces a structured explanation of the user's query."""
        clean_query = query.rstrip("?").strip()

        return (
            f"### 📖 Understanding: {clean_query}\n\n"
            f"**Subject Area:** {subject.title()}\n\n"
            f"**1. Core Idea:**\n"
            f"When examining **{clean_query}**, the fundamental principle revolves around understanding the underlying mechanism, its key variables, and how it connects to foundational rules in {subject}.\n\n"
            f"**2. Key Insights & Principles:**\n"
            f"• **Foundation:** Break the question down into essential components rather than memorizing isolated facts.\n"
            f"• **Application:** Observe how this principle behaves in practical scenarios and problem-solving.\n"
            f"• **Common Pitfalls:** Avoid skipping verification steps or assuming edge cases are identical to basic conditions.\n\n"
            f"**3. Practical Takeaway:**\n"
            f"To master this concept, try explaining the mechanism in your own words or applying it to a sample case."
        )

    def _build_structured_lesson(self, topic: str, emotion: str, message: str, strict: bool) -> Dict[str, Any]:
        """Constructs an explicit curriculum or quiz only when asked for."""
        difficulty = "Medium"
        steps = [
            "1. Define the fundamental theorems and definitions.",
            "2. Analyze solved sample problems demonstrating application.",
            "3. Complete active recall practice items.",
            "4. Verify results with step-by-step checklists.",
        ]

        coaching = self._coaching_line(emotion)
        coaching_str = f"\n{coaching}\n" if coaching else ""

        reply = (
            f"### 📚 Structured Study Module: {topic.replace('_', ' ').title()} ({difficulty})\n\n"
            f"**Learning Plan:**\n"
            + "\n".join(steps)
            + coaching_str
            + "\n\n**Practice Checkpoint:**\n"
            f"1. Explain the primary rule of `{topic}` in one sentence.\n"
            f"2. Apply this rule to solve a representative example.\n"
            f"3. What is the most common mistake made in this topic, and how do you prevent it?\n\n"
            "Reply with your thoughts, or type `#quiz` to test specific problem sets."
        )

        return {
            "agent": "teacher",
            "topic": topic,
            "reply": reply.strip(),
            "plan": {"style": f"Structured • {difficulty}", "steps": steps, "next_prompt": "Submit answers to proceed."},
        }
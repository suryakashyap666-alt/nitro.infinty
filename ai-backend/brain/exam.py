from __future__ import annotations

import random
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class ExamQuestion:
    qtype: str  # algebra|geometry|calculus|coding|general
    style: str  # IIT|CBSE
    level: str  # easy|medium|hard
    question: str
    steps: List[str]
    answer: str


class ExamEngine:
    """Never-seen question generator using deterministic templates."""

    def __init__(self) -> None:
        random.seed()

    def _parse_level_style(self, message: str) -> Tuple[str, str, str]:
        msg = message.lower()
        level = "medium"
        style = "IIT"
        qtype = "general"

        for lv in ["easy", "medium", "hard"]:
            if lv in msg:
                level = lv
                break

        if "cbse" in msg:
            style = "CBSE"

        if "algebra" in msg:
            qtype = "algebra"
        elif "geometry" in msg:
            qtype = "geometry"
        elif "calculus" in msg:
            qtype = "calculus"
        elif "coding" in msg:
            qtype = "coding"
        elif "math" in msg:
            qtype = "algebra"

        return qtype, style, level

    def handle_question(self, message: str) -> Tuple[str, Dict[str, Any]]:
        qtype, style, level = self._parse_level_style(message)
        q = self._generate_question(qtype=qtype, style=style, level=level)
        meta = {
            "question": q.question,
            "steps": q.steps,
            "answer": q.answer,
            "topic": q.qtype,
            "style": q.style,
            "level": q.level,
        }
        reply = self._format_question(q, include_steps_hint=True)
        return reply, meta

    def handle_answer(self, user_id: str, message: str) -> Tuple[str, Optional[Dict[str, Any]]]:
        # Commands: #answer <...>
        raw = message.strip()[len("#answer") :].strip()
        # Extract what user wrote; allow optional "Your answer:".
        ans = raw
        m = re.search(r"your\s*answer\s*[:\-]\s*(.*)$", raw, flags=re.I)
        if m:
            ans = m.group(1).strip()

        # Need last generated question; store in-memory? CoreBrain doesn't pass state.
        # We'll re-evaluate by embedding expected answer inside message if provided.
        # For robust operation, if user includes "Expected:" we validate; else we do a best-effort generic feedback.
        expected = None
        m2 = re.search(r"expected\s*[:\-]\s*(.*)$", raw, flags=re.I | re.S)
        if m2:
            expected = m2.group(1).strip()

        if expected is None:
            # Without expected answer, we ask user to show steps; but must avoid placeholders.
            reply = (
                "I received your answer. To evaluate it precisely, paste your full solution steps. "
                "Then use this format (optional): \n"
                "#answer <your answer> Expected: <expected final answer>\n"
                "Once I have the expected final answer, I’ll check correctness and teach where it goes wrong."
            )
            return reply, None

        is_correct = self._normalize(ans) == self._normalize(expected)
        eval_meta = {
            "correct": is_correct,
            "topic": "general",
            "user_answer": ans,
            "expected_answer": expected,
        }

        if is_correct:
            reply = (
                "Your final answer matches. ✅\n\n"
                "Want to improve further? I’ll give one extra practice variant at the same level. "
                "(Reply with #question easy/medium/hard as you like.)"
            )
        else:
            reply = (
                "Your final answer doesn’t match the expected one. ❌\n\n"
                "Send your working/steps (not just the final answer), and I’ll teach the key correction points step-by-step."
            )

        return reply, eval_meta

    def _format_question(self, q: ExamQuestion, include_steps_hint: bool) -> str:
        header = f"[Exam Trainer: {q.style} • {q.level} • {q.qtype.capitalize()}]"
        steps_hint = "\n\n(Show steps. I’ll evaluate and teach if wrong.)" if include_steps_hint else ""
        return header + "\n" + q.question + steps_hint

    def _generate_question(self, qtype: str, style: str, level: str) -> ExamQuestion:
        # Template-based generation to ensure variety and "never-seen" feel.
        # Uses random integers with constraints derived from level.
        if qtype not in {"algebra", "geometry", "calculus", "coding", "general"}:
            qtype = "general"
        if level not in {"easy", "medium", "hard"}:
            level = "medium"

        seed = random.randint(10, 10_000_000)
        rng = random.Random(seed)

        if qtype == "algebra":
            return self._algebra_question(style, level, rng)
        if qtype == "geometry":
            return self._geometry_question(style, level, rng)
        if qtype == "calculus":
            return self._calculus_question(style, level, rng)
        if qtype == "coding":
            return self._coding_question(style, level, rng)
        return self._general_question(style, level, rng)

    def _algebra_question(self, style: str, level: str, rng: random.Random) -> ExamQuestion:
        # Example: solve linear/quadratic with integer roots.
        if level == "easy":
            a = rng.randint(1, 9)
            b = rng.randint(1, 9)
            c = rng.randint(1, 9)
            # (a)x + b = c
            x = c - b
            question = f"Solve for x: {a}x + {b} = {c}."
            steps = [f"Subtract {b} from both sides:", f"{a}x = {c} - {b} = {x * a // a if a else x}" ]
            ans = str(x)
            steps = [
                f"Start: {a}x + {b} = {c}",
                f"Subtract {b}:",
                f"{a}x = {c - b}",
                f"Divide by {a}:",
                f"x = {(c - b) / a}",
            ]
            # ensure integer
            if (c - b) % a != 0:
                # regenerate quickly
                return self._algebra_question(style, "medium", rng)
            answer = str((c - b) // a)
            return ExamQuestion("algebra", style, level, question, steps, answer)

        if level == "medium":
            r1 = rng.randint(1, 9)
            r2 = rng.randint(1, 9)
            # (x-r1)(x-r2)=0 => x^2-(r1+r2)x+r1r2=0
            s = r1 + r2
            p = r1 * r2
            question = f"Find the solutions of x^2 - {s}x + {p} = 0."
            steps = [
                f"Factor the quadratic as (x - {r1})(x - {r2}) = 0",
                "Set each factor to zero:",
                f"x - {r1} = 0 → x = {r1}",
                f"x - {r2} = 0 → x = {r2}",
            ]
            answer = f"{r1}, {r2}"
            return ExamQuestion("algebra", style, level, question, steps, answer)

        # hard: two-step system
        x0 = rng.randint(2, 9)
        y0 = rng.randint(2, 9)
        # 2x+3y = ... and 4x+?y
        k = rng.randint(3, 7)
        a1, b1 = 2, 3
        c1 = a1 * x0 + b1 * y0
        a2, b2 = 4, k
        c2 = a2 * x0 + b2 * y0
        question = (
            f"Solve the system:\n"
            f"{a1}x + {b1}y = {c1}\n"
            f"{a2}x + {b2}y = {c2}"
        )
        steps = [
            "Use elimination:",
            f"Multiply first equation by {a2} and second by {a1} to eliminate x:",
            "Subtract to find y, then substitute back to find x.",
            f"Final: x = {x0}, y = {y0}",
        ]
        answer = f"x={x0}, y={y0}"
        return ExamQuestion("algebra", style, level, question, steps, answer)

    def _geometry_question(self, style: str, level: str, rng: random.Random) -> ExamQuestion:
        if level == "easy":
            r = rng.randint(3, 10)
            pi = 3.14
            area = pi * r * r
            question = f"Find the area of a circle with radius {r} cm. Use π ≈ {pi}."
            steps = [
                "Area of circle: A = πr²",
                f"A = {pi} × {r}²",
                f"A = {area} cm² (approx)",
            ]
            answer = f"{area:.2f}"
            return ExamQuestion("geometry", style, level, question, steps, answer)

        if level == "medium":
            a = rng.randint(3, 9)
            b = rng.randint(4, 12)
            # rectangle area/perimeter
            question = f"A rectangle has length {a} cm and breadth {b} cm. Find its perimeter."
            perimeter = 2 * (a + b)
            steps = [
                "Perimeter of rectangle: P = 2(l + b)",
                f"P = 2({a} + {b})",
                f"P = {perimeter} cm",
            ]
            answer = str(perimeter)
            return ExamQuestion("geometry", style, level, question, steps, answer)

        # hard: triangle angles sum
        A = rng.randint(20, 60)
        B = rng.randint(20, 70)
        C = 180 - A - B
        question = f"In triangle ABC, angles A and B are {A}° and {B}° respectively. Find angle C."
        steps = [
            "Sum of angles in a triangle is 180°",
            f"C = 180° - ({A}° + {B}°)",
            f"C = {C}°",
        ]
        answer = str(C)
        return ExamQuestion("geometry", style, level, question, steps, answer)

    def _calculus_question(self, style: str, level: str, rng: random.Random) -> ExamQuestion:
        # Provide derivative of polynomial and/or basic integral.
        if level == "easy":
            a = rng.randint(1, 8)
            n = rng.randint(2, 5)
            # d/dx (a x^n) = a n x^(n-1)
            question = f"Differentiate: d/dx ( {a}x^{n} )."
            steps = [
                "Use power rule: d/dx (x^n) = n x^(n-1)",
                f"d/dx({a}x^{n}) = {a} × {n}x^({n}-1)",
                f"Answer: {a*n}x^{n-1}",
            ]
            answer = f"{a*n}x^{n-1}"
            return ExamQuestion("calculus", style, level, question, steps, answer)

        if level == "medium":
            a = rng.randint(1, 5)
            b = rng.randint(1, 5)
            # integral a x + b = a x^2/2 + b x
            question = f"Evaluate: ∫ ({a}x + {b}) dx."
            steps = [
                "Integrate term-by-term:",
                f"∫ {a}x dx = {a} * x^2/2",
                f"∫ {b} dx = {b}x",
                "Add constant C (optional).",
            ]
            answer = f"{a/2}x^2 + {b}x"  # string
            return ExamQuestion("calculus", style, level, question, steps, answer)

        # hard: derivative of product simple
        m = rng.randint(2, 5)
        n = rng.randint(2, 5)
        question = f"Differentiate: d/dx ( x^{m} · x^{n} )."
        # simplify x^{m+n}
        k = m + n
        answer = f"{k}x^{k-1}"
        steps = [
            "Combine exponents: x^m · x^n = x^(m+n)",
            f"So expression becomes x^{k}",
            "Apply power rule:",
            f"d/dx(x^{k}) = {k}x^{k-1}",
        ]
        return ExamQuestion("calculus", style, level, question, steps, answer)

    def _coding_question(self, style: str, level: str, rng: random.Random) -> ExamQuestion:
        # Coding exam style: algorithm output.
        if level == "easy":
            n = rng.randint(5, 15)
            question = (
                f"Write a function that takes a list of {n} integers and returns the maximum value. "
                "Constraints: do not sort the list."
            )
            steps = [
                "Initialize max_val to the first element.",
                "Iterate through remaining elements and update max_val when a larger value is found.",
                "Return max_val.",
            ]
            answer = "max"  # meta answer
            return ExamQuestion("coding", style, level, question, steps, answer)

        if level == "medium":
            target = rng.randint(3, 9)
            question = (
                f"Given an array, find indices of two numbers that add up to {target}. "
                "Return the pair as (i, j) with i < j."
            )
            steps = [
                "Use a hash map from value to index.",
                "For each number x at index i, compute complement = target - x.",
                "If complement exists in map, return (index_of_complement, i).",
            ]
            answer = "hash-map-two-sum"
            return ExamQuestion("coding", style, level, question, steps, answer)

        # hard
        question = (
            "Implement a Least Recently Used (LRU) cache of capacity k. "
            "Operations: get(key), put(key,value)."
        )
        steps = [
            "Use a doubly linked list to track recency and a dict for O(1) lookup.",
            "On get/put of an existing key, move node to front as most recent.",
            "On capacity overflow, evict least recent node from tail.",
        ]
        answer = "LRU-DLL+dict"
        return ExamQuestion("coding", style, level, question, steps, answer)

    def _general_question(self, style: str, level: str, rng: random.Random) -> ExamQuestion:
        # General reasoning prompt.
        if level == "easy":
            question = "Explain in 3-4 lines the difference between 'factor' and 'multiple' in mathematics."
            steps = ["Define factor", "Define multiple", "Give a short example", "Summarize"]
            answer = "definition+example"
            return ExamQuestion("general", style, level, question, steps, answer)

        if level == "medium":
            question = "Provide a step-by-step approach to solve a quadratic equation when it is not factorable."
            steps = ["Use standard form", "Use quadratic formula", "Substitute values", "Simplify & interpret roots"]
            answer = "quadratic-formula"
            return ExamQuestion("general", style, level, question, steps, answer)

        question = "How would you verify your answer after solving a problem? Give a systematic checklist."
        steps = ["Check units", "Re-substitute", "Try extreme cases", "Confirm with alternative method"]
        answer = "verification-checklist"
        return ExamQuestion("general", style, level, question, steps, answer)

    def _normalize(self, s: str) -> str:
        return " ".join(s.strip().lower().split())


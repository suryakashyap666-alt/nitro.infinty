from __future__ import annotations

import math
import re
from typing import Any, Callable, Dict, List, Optional, Tuple


class MathEngine:
    """Mathematical solver and step-by-step evaluator for Nitro Infinity AI.

    Evaluates arithmetic, linear equations, basic calculus, power/roots,
    and formats comprehensive step-by-step educational responses without external models.
    """

    def __init__(self) -> None:
        pass

    def is_math_expression(self, text: str) -> bool:
        """Heuristic check to determine if text is primarily a mathematical problem."""
        t = (text or "").strip().lower()
        if not t:
            return False

        # Command markers
        if t.startswith(("#solve", "solve", "calculate", "compute", "evaluate", "simplify")):
            return True

        # Common math keywords
        math_keywords = [
            "derivative",
            "differentiate",
            "integral",
            "integrate",
            "algebra",
            "quadratic",
            "square root",
            "sqrt",
            "factorial",
            "equation",
            "polynomial",
            "logarithm",
        ]
        if any(k in t for k in math_keywords):
            return True

        # Contains numbers and mathematical operators
        has_digits = bool(re.search(r"\d", t))
        has_operators = bool(re.search(r"[+\-*/^=√%]", t))
        if has_digits and has_operators:
            return True

        return False

    def solve(
        self,
        payload: str,
        user_id: str = "",
        as_teaching: bool = True,
        web_context_data: Optional[List[Dict[str, str]]] = None,
        progress_callback: Callable[[int], None] | None = None,
    ) -> Dict[str, Any]:
        def _progress(value: int) -> None:
            if progress_callback is None:
                return
            try:
                progress_callback(max(0, min(100, int(value))))
            except Exception:
                pass

        _progress(10)
        raw_text = (payload or "").strip()

        # Handle prompt format from LearningEngine
        if raw_text.lower().startswith("topic:"):
            res = self._solve_prompt_format(raw_text, as_teaching=as_teaching)
            _progress(100)
            return res

        # Strip common instruction prefixes
        clean_expr = re.sub(
            r"^(#solve|solve for [a-z]|solve|calculate|what is the value of|what is|compute|evaluate)\s*",
            "",
            raw_text,
            flags=re.IGNORECASE,
        ).strip().rstrip("?").strip()

        _progress(30)

        # 1. Check for Calculus (Derivatives)
        if "derivative" in raw_text.lower() or "d/dx" in raw_text.lower() or "differentiate" in raw_text.lower():
            res = self._solve_derivative(clean_expr, raw_text)
            _progress(100)
            return res

        # 2. Check for Single Variable Linear Equations (e.g. 2x + 5 = 15)
        if "=" in clean_expr and re.search(r"[a-zA-Z]", clean_expr):
            res = self._solve_linear_equation(clean_expr)
            if res.get("correct"):
                _progress(100)
                return res

        # 3. Check for Square Roots / Power functions
        clean_expr_normalized = self._normalize_expression(clean_expr)

        _progress(60)
        # 4. Standard Arithmetic & Expression Evaluation
        try:
            val, steps = self._evaluate_arithmetic_with_steps(clean_expr_normalized)
            ans_str = str(int(val)) if float(val).is_integer() else f"{val:.4f}".rstrip("0").rstrip(".")

            explanation = [
                f"**Problem:** Evaluate `{clean_expr}`",
                "",
                "**Step-by-step Solution:**",
            ]
            for idx, st in enumerate(steps, 1):
                explanation.append(f"{idx}. {st}")

            explanation.append("")
            explanation.append(f"**Final Answer:** `{ans_str}`")

            if web_context_data:
                explanation.append("")
                explanation.append("*(Verified through native mathematical analysis)*")

            _progress(100)
            return {
                "topic": "algebra",
                "correct": True,
                "mistake": False,
                "reply": "\n".join(explanation),
                "answer": val,
            }
        except Exception as e:
            # Fallback handling
            _progress(100)
            return {
                "topic": "algebra",
                "correct": False,
                "mistake": True,
                "reply": self._format_error(clean_expr, str(e), as_teaching=as_teaching),
                "error": str(e),
            }

    def _normalize_expression(self, expr: str) -> str:
        s = expr.replace("×", "*").replace("÷", "/").replace("−", "-")
        s = re.sub(r"sqrt\s*\(([^)]+)\)", r"(\1)^0.5", s, flags=re.I)
        s = re.sub(r"square root of\s*(\d+(\.\d+)?)", r"(\1)^0.5", s, flags=re.I)
        s = re.sub(r"(\d+)%", r"(\1/100)", s)
        return s

    def _solve_derivative(self, expr: str, full_query: str) -> Dict[str, Any]:
        """Simple polynomial derivative solver (e.g. 3x^2 + 5x - 4)."""
        target = expr
        m = re.search(r"(?:derivative of|differentiate|d/dx)\s*[:]?\s*(.+)", full_query, flags=re.I)
        if m:
            target = m.group(1).strip().rstrip("?").strip()

        target_norm = target.replace(" ", "")
        # Match polynomial terms like ax^n, ax, or constant
        terms = re.findall(r"([+-]?\s*\d*\.?\d*)\s*(?:([a-zA-Z])(?:\^([+-]?\d+))?)?", target)

        steps: List[str] = [
            f"Apply the Power Rule of Differentiation: `d/dx [a*x^n] = a*n*x^(n-1)`",
            f"Differentiate each term in `{target}` with respect to the variable:",
        ]

        derived_terms: List[str] = []
        for coeff_str, var, exp_str in terms:
            coeff_str = coeff_str.replace(" ", "")
            if not coeff_str and not var:
                continue

            # Determine coefficient
            if coeff_str in ("", "+"):
                coeff = 1.0
            elif coeff_str == "-":
                coeff = -1.0
            else:
                try:
                    coeff = float(coeff_str)
                except ValueError:
                    coeff = 1.0

            # Constant term
            if not var:
                steps.append(f"• Derivative of constant `{coeff_str}` is `0`")
                continue

            # Linear term ax
            if not exp_str:
                derived_terms.append(f"{coeff:g}")
                steps.append(f"• Derivative of `{coeff_str or ''}{var}` is `{coeff:g}`")
                continue

            # Power term ax^n
            power = float(exp_str)
            new_coeff = coeff * power
            new_power = power - 1

            if new_power == 1:
                term_repr = f"{new_coeff:g}{var}"
            elif new_power == 0:
                term_repr = f"{new_coeff:g}"
            else:
                term_repr = f"{new_coeff:g}{var}^{new_power:g}"

            derived_terms.append(term_repr)
            steps.append(f"• Derivative of `{coeff_str or ''}{var}^{exp_str}` is `{new_coeff:g}{var}^{new_power:g}`")

        final_res = " + ".join(derived_terms).replace("+ -", "- ") or "0"

        reply = (
            f"**Problem:** Compute derivative of `{target}`\n\n"
            f"**Step-by-step Solution:**\n"
            + "\n".join([f"{i+1}. {s}" for i, s in enumerate(steps)])
            + f"\n\n**Final Answer:** `{final_res}`"
        )
        return {"topic": "calculus", "correct": True, "mistake": False, "reply": reply, "answer": final_res}

    def _solve_linear_equation(self, expr: str) -> Dict[str, Any]:
        """Solves linear equations like ax + b = c."""
        sides = expr.split("=")
        if len(sides) != 2:
            return {"correct": False}

        left, right = sides[0].strip(), sides[1].strip()
        var_match = re.search(r"[a-zA-Z]", left) or re.search(r"[a-zA-Z]", right)
        if not var_match:
            return {"correct": False}

        var = var_match.group(0)

        # Standard simple form: ax + b = c
        steps: List[str] = [
            f"Given linear equation: `{left} = {right}`",
            f"Group variable terms with `{var}` on one side and constants on the other.",
        ]

        # Check standard format: [a]x + [b] = [c]
        pattern = rf"([+-]?\s*\d*\.?\d*)\s*{var}\s*([+-]\s*\d+\.?\d*)?"
        m_left = re.match(pattern, left)
        if m_left and right.replace(".", "", 1).replace("-", "", 1).isdigit():
            c_val = float(right)
            a_str = (m_left.group(1) or "1").replace(" ", "")
            b_str = (m_left.group(2) or "0").replace(" ", "")

            a_val = -1.0 if a_str == "-" else (1.0 if a_str in ("", "+") else float(a_str))
            b_val = float(b_str)

            steps.append(f"Subtract constant `{b_val:g}` from both sides: `{a_val:g}{var} = {c_val - b_val:g}`")
            sol = (c_val - b_val) / a_val
            steps.append(f"Divide both sides by `{a_val:g}`: `{var} = {sol:g}`")

            ans_str = f"{var} = {int(sol)}" if sol.is_integer() else f"{var} = {sol:.4f}".rstrip("0").rstrip(".")

            reply = (
                f"**Problem:** Solve for `{var}` in `{expr}`\n\n"
                f"**Step-by-step Solution:**\n"
                + "\n".join([f"{i+1}. {s}" for i, s in enumerate(steps)])
                + f"\n\n**Final Answer:** `{ans_str}`"
            )
            return {"topic": "algebra", "correct": True, "mistake": False, "reply": reply, "answer": sol}

        return {"correct": False}

    def _evaluate_arithmetic_with_steps(self, expr: str) -> Tuple[float, List[str]]:
        """Safe arithmetic parser implementing Shunting-Yard with step descriptions."""
        s = expr.replace(" ", "")
        if not s:
            raise ValueError("Empty expression")

        if not re.fullmatch(r"[0-9+\-*/().\^]+", s):
            raise ValueError("Expression contains unsupported characters")

        steps: List[str] = [
            f"Parse mathematical expression: `{expr}`",
            "Identify order of operations (Parentheses, Exponents, Multiplication & Division, Addition & Subtraction).",
        ]

        # Tokenize
        tokens = re.findall(r"\d+\.?\d*|[+\-*/()^]", s)
        prec = {"+": 1, "-": 1, "*": 2, "/": 2, "^": 3}

        output: List[str] = []
        ops: List[str] = []

        for t in tokens:
            if re.match(r"^\d+\.?\d*$", t):
                output.append(t)
            elif t in prec:
                while ops and ops[-1] in prec and prec[ops[-1]] >= prec[t]:
                    output.append(ops.pop())
                ops.append(t)
            elif t == "(":
                ops.append(t)
            elif t == ")":
                while ops and ops[-1] != "(":
                    output.append(ops.pop())
                if not ops or ops[-1] != "(":
                    raise ValueError("Mismatched parentheses")
                ops.pop()

        while ops:
            op = ops.pop()
            if op in "()":
                raise ValueError("Mismatched parentheses")
            output.append(op)

        stack: List[float] = []
        eval_steps_summary: List[str] = []

        for item in output:
            if re.match(r"^\d+\.?\d*$", item):
                stack.append(float(item))
            else:
                if len(stack) < 2:
                    raise ValueError("Invalid expression format")
                b = stack.pop()
                a = stack.pop()
                if item == "+":
                    res = a + b
                elif item == "-":
                    res = a - b
                elif item == "*":
                    res = a * b
                elif item == "/":
                    if b == 0:
                        raise ZeroDivisionError("Division by zero")
                    res = a / b
                elif item == "^":
                    res = math.pow(a, b)
                else:
                    raise ValueError(f"Unknown operator: {item}")

                stack.append(res)
                eval_steps_summary.append(f"Calculate `{a:g} {item} {b:g}` = `{res:g}`")

        if len(stack) != 1:
            raise ValueError("Evaluation did not reduce to a single value")

        steps.extend(eval_steps_summary)
        return stack[0], steps

    def _solve_prompt_format(self, prompt: str, as_teaching: bool) -> Dict[str, Any]:
        topic = self._extract_kv(prompt, "Topic") or "algebra"
        difficulty = self._extract_kv(prompt, "Difficulty") or "medium"

        if difficulty == "easy":
            expr = "(3 + 5) * 2"
        elif difficulty == "hard":
            expr = "(18 / 3 + 7) * 2"
        else:
            expr = "(10 - 4) * (3 + 2)"

        val, steps = self._evaluate_arithmetic_with_steps(expr)

        reply = (
            f"**Practice ({topic.capitalize()} • {difficulty.capitalize()}):**\n\n"
            f"Solve the expression: `{expr}`\n\n"
            f"**Hint:** Evaluate operations inside parentheses first, then apply multiplication."
        )
        return {
            "topic": topic,
            "correct": False,
            "mistake": False,
            "reply": reply,
            "prompt_expr": expr,
            "expected_answer": val,
        }

    def _extract_kv(self, prompt: str, key: str) -> Optional[str]:
        m = re.search(rf"{re.escape(key)}\s*:\s*([^;]+)", prompt, flags=re.I)
        return m.group(1).strip() if m else None

    def _format_error(self, expr: str, error: str, as_teaching: bool) -> str:
        return (
            f"**Calculation Error**\n\n"
            f"Unable to safely evaluate: `{expr}`\n"
            f"**Reason:** {error}\n\n"
            f"Please verify numbers and operators (supported: `+`, `-`, `*`, `/`, `^`, `sqrt`, parentheses, and linear equations)."
        )
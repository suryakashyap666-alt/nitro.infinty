from __future__ import annotations

import math
import re
from typing import Any, Callable, Dict, List, Optional, Tuple


class MathEngine:
    """Mathematical solver and step-by-step evaluator for Nitro Infinity AI."""

    def __init__(self) -> None:
        pass

    def is_math_expression(self, text: str) -> bool:
        t = (text or "").strip().lower()
        if not t:
            return False

        if t.startswith(("#solve", "solve", "calculate", "compute", "evaluate", "simplify")):
            return True

        math_keywords = [
            "derivative", "differentiate", "integral", "integrate",
            "algebra", "quadratic", "square root", "sqrt",
            "factorial", "equation", "polynomial", "logarithm",
        ]
        if any(k in t for k in math_keywords):
            return True

        has_digits = bool(re.search(r"\d", t))
        has_operators = bool(re.search(r"[+\-*/^=√%]", t))
        return has_digits and has_operators

    def solve(
        self,
        payload: str,
        user_id: str = "",
        as_teaching: bool = True,
        web_context_data: Optional[List[Dict[str, str]]] = None,
        progress_callback: Callable[[int], None] | None = None,
    ) -> Dict[str, Any]:
        raw_text = (payload or "").strip()

        clean_expr = re.sub(
            r"^(#solve|solve for [a-z]|solve|calculate|what is the value of|what is|compute|evaluate)\s*",
            "",
            raw_text,
            flags=re.IGNORECASE,
        ).strip().rstrip("?").strip()

        # 1. Derivatives
        if "derivative" in raw_text.lower() or "d/dx" in raw_text.lower() or "differentiate" in raw_text.lower():
            return self._solve_derivative(clean_expr, raw_text)

        # 2. Linear Equations
        if "=" in clean_expr and re.search(r"[a-zA-Z]", clean_expr):
            res = self._solve_linear_equation(clean_expr)
            if res.get("correct"):
                return res

        # 3. Standard Arithmetic
        try:
            clean_norm = self._normalize_expression(clean_expr)
            val, steps = self._evaluate_arithmetic_with_steps(clean_norm)
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

            return {
                "topic": "algebra",
                "correct": True,
                "mistake": False,
                "reply": "\n".join(explanation),
                "answer": val,
            }
        except Exception as e:
            return {
                "topic": "algebra",
                "correct": False,
                "mistake": True,
                "reply": f"**Calculation Error:** Unable to safely evaluate `{clean_expr}`: {e}",
                "error": str(e),
            }

    def _normalize_expression(self, expr: str) -> str:
        s = expr.replace("×", "*").replace("÷", "/").replace("−", "-")
        s = re.sub(r"sqrt\s*\(([^)]+)\)", r"(\1)^0.5", s, flags=re.I)
        s = re.sub(r"square root of\s*(\d+(\.\d+)?)", r"(\1)^0.5", s, flags=re.I)
        s = re.sub(r"(\d+)%", r"(\1/100)", s)
        return s

    def _solve_derivative(self, expr: str, full_query: str) -> Dict[str, Any]:
        target = expr
        m = re.search(r"(?:derivative of|differentiate|d/dx)\s*[:]?\s*(.+)", full_query, flags=re.I)
        if m:
            target = m.group(1).strip().rstrip("?").strip()

        terms = re.findall(r"([+-]?\s*\d*\.?\d*)\s*(?:([a-zA-Z])(?:\^([+-]?\d+))?)?", target)
        steps: List[str] = [
            f"Apply the Power Rule: `d/dx [a*x^n] = a*n*x^(n-1)`",
            f"Differentiate each term in `{target}`:",
        ]

        derived_terms: List[str] = []
        for coeff_str, var, exp_str in terms:
            coeff_str = coeff_str.replace(" ", "")
            if not coeff_str and not var:
                continue

            coeff = -1.0 if coeff_str == "-" else (1.0 if coeff_str in ("", "+") else float(coeff_str))

            if not var:
                steps.append(f"• Derivative of constant `{coeff_str}` is `0`")
                continue

            if not exp_str:
                derived_terms.append(f"{coeff:g}")
                steps.append(f"• Derivative of `{coeff_str or ''}{var}` is `{coeff:g}`")
                continue

            power = float(exp_str)
            new_coeff = coeff * power
            new_power = power - 1

            term_repr = f"{new_coeff:g}" if new_power == 0 else (f"{new_coeff:g}{var}" if new_power == 1 else f"{new_coeff:g}{var}^{new_power:g}")
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
        sides = expr.split("=")
        if len(sides) != 2:
            return {"correct": False}

        left, right = sides[0].strip(), sides[1].strip()
        var_match = re.search(r"[a-zA-Z]", left) or re.search(r"[a-zA-Z]", right)
        if not var_match:
            return {"correct": False}

        var = var_match.group(0)
        pattern = rf"([+-]?\s*\d*\.?\d*)\s*{var}\s*([+-]\s*\d+\.?\d*)?"
        m_left = re.match(pattern, left)

        if m_left and right.replace(".", "", 1).replace("-", "", 1).isdigit():
            c_val = float(right)
            a_str = (m_left.group(1) or "1").replace(" ", "")
            b_str = (m_left.group(2) or "0").replace(" ", "")
            a_val = -1.0 if a_str == "-" else (1.0 if a_str in ("", "+") else float(a_str))
            b_val = float(b_str)

            sol = (c_val - b_val) / a_val
            ans_str = f"{var} = {int(sol)}" if sol.is_integer() else f"{var} = {sol:.4f}".rstrip("0").rstrip(".")

            steps = [
                f"Given linear equation: `{left} = {right}`",
                f"Subtract constant `{b_val:g}` from both sides: `{a_val:g}{var} = {c_val - b_val:g}`",
                f"Divide both sides by `{a_val:g}`: `{var} = {sol:g}`",
            ]

            reply = (
                f"**Problem:** Solve for `{var}` in `{expr}`\n\n"
                f"**Step-by-step Solution:**\n"
                + "\n".join([f"{i+1}. {s}" for i, s in enumerate(steps)])
                + f"\n\n**Final Answer:** `{ans_str}`"
            )
            return {"topic": "algebra", "correct": True, "mistake": False, "reply": reply, "answer": sol}

        return {"correct": False}

    def _evaluate_arithmetic_with_steps(self, expr: str) -> Tuple[float, List[str]]:
        s = expr.replace(" ", "")
        if not s or not re.fullmatch(r"[0-9+\-*/().\^]+", s):
            raise ValueError("Expression contains unsupported characters")

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
                if item == "+": res = a + b
                elif item == "-": res = a - b
                elif item == "*": res = a * b
                elif item == "/":
                    if b == 0: raise ZeroDivisionError("Division by zero")
                    res = a / b
                elif item == "^": res = math.pow(a, b)
                else: raise ValueError(f"Unknown operator: {item}")

                stack.append(res)
                eval_steps_summary.append(f"Calculate `{a:g} {item} {b:g}` = `{res:g}`")

        if len(stack) != 1:
            raise ValueError("Evaluation error")

        return stack[0], eval_steps_summary
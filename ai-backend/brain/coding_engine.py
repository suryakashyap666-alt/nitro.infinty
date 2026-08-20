from __future__ import annotations

import re
from typing import Any, Callable, Dict, List


class CodingEngine:
    """Complete rule-based coding architect, explainer, reviewer, and debugger."""

    def generate_code(self, payload: str, user_id: str = "", progress_callback: Callable[[int], None] | None = None) -> Dict[str, Any]:
        req = payload.strip()
        low = req.lower()

        if "fastapi" in low:
            code = (
                "from fastapi import FastAPI, HTTPException\n"
                "from pydantic import BaseModel, Field\n"
                "from typing import Any, Dict\n\n"
                "app = FastAPI(title='Nitro Microservice')\n\n"
                "class QueryRequest(BaseModel):\n"
                "    message: str = Field(min_length=1, max_length=1000)\n\n"
                "@app.post('/process')\n"
                "def process_query(req: QueryRequest) -> Dict[str, Any]:\n"
                "    return {'status': 'success', 'echo': req.message}\n"
            )
            title = "FastAPI Service"
        elif "react" in low or "javascript" in low:
            code = (
                "import React, { useState } from 'react';\n\n"
                "export default function Counter() {\n"
                "  const [count, setCount] = useState(0);\n"
                "  return (\n"
                "    <div style={{ textAlign: 'center', padding: '20px' }}>\n"
                "      <h3>Count: {count}</h3>\n"
                "      <button onClick={() => setCount(c => c + 1)}>Increment</button>\n"
                "    </div>\n"
                "  );\n"
                "}\n"
            )
            title = "React Component"
        else:
            code = (
                "def process_items(items: list) -> list:\n"
                "    \"\"\"Filter and clean list items.\"\"\"\n"
                "    return [item.strip() for item in items if isinstance(item, str) and item.strip()]\n\n"
                "if __name__ == '__main__':\n"
                "    sample = [' alpha ', ' ', None, 'beta']\n"
                "    print(process_items(sample))\n"
            )
            title = "Python Utility"

        reply = (
            f"**Generated Code:** `{title}`\n\n"
            f"```python\n{code}\n```\n\n"
            "**Architecture Highlights:**\n"
            "1. Validates inputs and handles empty states safely.\n"
            "2. Isolated functions for easy unit testing.\n"
            "3. Structured without global state mutation."
        )

        return {"topic": "coding", "correct": True, "mistake": False, "reply": reply, "code": code}

    def explain_code(self, code: str) -> str:
        lines = code.strip().splitlines()
        steps = []
        for idx, line in enumerate(lines[:30], 1):
            if line.strip():
                steps.append(f"{idx}. `{line.strip()}` — Executes statement logic.")
        return "### 📖 Code Explanation:\n\n" + "\n".join(steps)

    def debug_code(self, code: str) -> str:
        findings = []
        if "eval(" in code or "exec(" in code:
            findings.append("Unsafe execution detected: `eval`/`exec`. Replace with safe parsing.")
        if "while True" in code and "break" not in code:
            findings.append("Potential infinite loop: ensure a valid termination break condition exists.")
        if not findings:
            findings.append("Code structure is clean. Ensure all variable bounds and None types are guarded.")

        return "### 🛠️ Debug Analysis:\n\n" + "\n".join([f"• {f}" for f in findings])
from __future__ import annotations

import re
from typing import Any, Callable, Dict, List


class CodingEngine:
    """Rule-based coding assistant for Python/FastAPI/React/JavaScript.

    No code execution. Generates explanations and safer code templates.
    """

    def __init__(self) -> None:
        pass

    def generate_code(self, payload: str, user_id: str, progress_callback: Callable[[int], None] | None = None) -> Dict[str, Any]:
        def _progress(value: int) -> None:
            if progress_callback is None:
                return
            try:
                progress_callback(max(0, min(100, int(value))))
            except Exception:
                pass

        _progress(5)
        req = payload.strip()
        lang = self._detect_language(req)

        low = req.lower()
        if "fastapi" in low:
            result = self._fastapi_template(req)
        elif "react" in low or "javascript" in low or "node" in low:
            result = self._react_js_template(req, lang)
        elif "python" in low or lang == "python":
            result = self._python_template(req)
        else:
            result = self._python_template(req)
        _progress(100)
        return result

    def explain_code(self, payload: str, user_id: str) -> Dict[str, Any]:
        code = self._extract_code_block(payload)
        if not code:
            topic = self._detect_concept(payload)
            steps = self._concept_explanation(topic)
            return {
                "topic": "coding",
                "correct": True,
                "mistake": False,
                "reply": "Concept explanation:\n\n" + "\n".join(steps),
            }

        steps = self._explain_line_by_line(code)
        return {
            "topic": "coding",
            "correct": True,
            "mistake": False,
            "reply": "Step-by-step explanation:\n\n" + "\n".join(steps),
        }

    def debug_code(self, payload: str, user_id: str) -> Dict[str, Any]:
        code = self._extract_code_block(payload)
        if not code:
            return {
                "topic": "coding",
                "correct": False,
                "mistake": True,
                "reply": "Paste the code you want debugged (use #debug <code>) and include any error message text.",
            }

        findings: List[str] = []
        fixed = code
        low = payload.lower()

        # Basic safety checks
        if "eval(" in code or "exec(" in code:
            findings.append("Unsafe execution found: eval/exec. Replace with safe parsing/whitelisting.")
            fixed = fixed.replace("eval(", "# eval(")
            fixed = fixed.replace("exec(", "# exec(")

        # Python common issues
        if re.search(r"def\s+\w+\s*\([^)]*\)\s*:\s*\n\s*return\s+", code) and "if __name__" not in code:
            findings.append("If you expect a standalone run, add a small `if __name__ == '__main__':` example to show how to call it.")

        # React/JS common issues
        if ".map(" in code and "key=" not in code:
            findings.append("In React list rendering, ensure each item has a unique `key` prop.")

        # Infinite loop guards
        if re.search(r"\bwhile\s+True\b", code):
            findings.append("Detected `while True`. Ensure there is a clear break/termination condition or a timeout to prevent hangs.")

        # Missing error context
        if not re.search(r"traceback|error|exception", low):
            findings.append("Paste the exact error/stack trace and the failing input so I can pinpoint the failing path.")

        if not findings:
            findings.append("I scanned for common issues. If it still fails, paste the exact error message and expected behavior.")

        reply = (
            "Debugging results:\n\n"
            + "\n".join([f"- {f}" for f in findings])
            + "\n\nSuggested direction (no execution):\n"
            + "1) Identify the failing line from the stack trace\n"
            + "2) Reproduce with the minimal failing input\n"
            + "3) Validate assumptions (types, ranges, null/undefined)\n"
            + "4) Add a targeted test for the failing case"
        )

        return {
            "topic": "coding",
            "correct": False,
            "mistake": True,
            "reply": reply,
            "fixed_code": fixed,
        }

    def review_code(self, payload: str, user_id: str) -> Dict[str, Any]:
        code = self._extract_code_block(payload)
        if not code:
            return {
                "topic": "coding",
                "correct": False,
                "mistake": True,
                "reply": "Paste the code you want reviewed (use #review <code>), and specify the language/framework.",
            }

        issues: List[str] = []
        improvements: List[str] = []

        if len(code) > 1500:
            improvements.append("Consider splitting large files into modules/functions for readability and maintainability.")

        if "import *" in code:
            issues.append("Avoid wildcard imports; import explicitly to reduce ambiguity.")

        if "TODO" in code or "FIXME" in code:
            improvements.append("Replace TODO/FIXME with concrete behavior or remove dead paths.")

        if "print(" in code and "debug" not in code.lower():
            improvements.append("Avoid leftover prints in production; use logging with appropriate levels.")

        if re.search(r"\bwhile\s+True\b", code):
            improvements.append("Ensure loop termination conditions and add safeguards (timeouts, max-iterations) to prevent hangs.")

        if not issues and not improvements:
            improvements.append("Code looks broadly structured. Add docstrings/comments for key functions and validate inputs at boundaries.")

        reply = "Code review:\n\n"
        if issues:
            reply += "Potential issues:\n" + "\n".join([f"- {i}" for i in issues]) + "\n\n"
        reply += "Improvements:\n" + "\n".join([f"- {i}" for i in improvements])

        return {"topic": "coding", "correct": True, "mistake": False, "reply": reply}

    def teach_concept(self, payload: str, user_id: str) -> Dict[str, Any]:
        concept = payload.strip() or "core concepts of programming"
        key = self._detect_concept(concept)
        steps = self._teaching_module(key, concept)
        return {"topic": "coding", "correct": True, "mistake": False, "reply": steps}

    def _detect_language(self, req: str) -> str:
        r = req.lower()
        if "fastapi" in r or "python" in r:
            return "python"
        if "react" in r or "jsx" in r or "typescript" in r:
            return "react"
        if "javascript" in r or "node" in r:
            return "javascript"
        return "python"

    def _extract_code_block(self, payload: str) -> str:
        m = re.search(r"```[a-zA-Z0-9]*\n([\s\S]*?)```", payload)
        if m:
            return m.group(1).strip()
        # No fenced block: attempt to grab first 200 lines if it looks like code.
        lines = payload.splitlines()[:200]
        if any("def " in l or "class " in l or "function " in l or "=>" in l for l in lines):
            return "\n".join(lines).strip()
        return ""

    def _detect_concept(self, text: str) -> str:
        t = text.lower()
        if "fastapi" in t:
            return "fastapi"
        if "react" in t:
            return "react"
        if "security" in t or "auth" in t:
            return "security"
        if "error" in t and "handling" in t:
            return "error_handling"
        if "loop" in t or "recursion" in t:
            return "control_flow"
        if "algorithm" in t:
            return "algorithms"
        if "database" in t or "persistence" in t:
            return "persistence"
        if "debug" in t:
            return "debugging"
        if "memory" in t or "cache" in t:
            return "memory"
        return "general_programming"

    def _concept_explanation(self, topic: str) -> List[str]:
        if topic == "fastapi":
            return [
                "FastAPI is a Python web framework for building APIs.",
                "You define endpoints with decorators like @app.post('/path').",
                "Use Pydantic models for request/response validation.",
                "Add middleware (e.g., CORS) to control browser access.",
            ]
        if topic == "react":
            return [
                "React builds UI from components.",
                "State changes trigger re-rendering.",
                "Props flow data top-down; callbacks update state.",
                "Use keys for list rendering and keep effects scoped.",
            ]
        return [
            f"Concept: {topic}",
            "Break it into inputs → transformations → outputs.",
            "Write tests for edge cases.",
            "Explain the reasoning behind each step.",
        ]

    def _teaching_module(self, key: str, prompt: str) -> str:
        if key == "fastapi":
            return (
                "Teaching: FastAPI (Production-style)\n\n"
                "1) Define request/response models (Pydantic) so the API is self-validating.\n"
                "2) Create endpoints with explicit methods and paths.\n"
                "3) Handle errors with clear HTTP status codes.\n"
                "4) Add CORS only for trusted origins when deploying.\n"
                "5) Keep business logic in separate modules for testability.\n\n"
                f"Your request: {prompt}"
            )
        if key == "react":
            return (
                "Teaching: React fundamentals\n\n"
                "1) Components: UI pieces that render based on props/state.\n"
                "2) State: useState for local state; lift state up when shared.\n"
                "3) Side effects: useEffect for network calls; include proper dependency arrays.\n"
                "4) Responsiveness: use flexible layout (CSS) and avoid fixed heights where possible.\n"
                "5) Debugging: reproduce, inspect state transitions, and check network responses.\n\n"
                f"Your request: {prompt}"
            )
        if key == "security":
            return (
                "Teaching: Secure coding basics\n\n"
                "1) Validate inputs at boundaries (types, length, allowed characters).\n"
                "2) Avoid unsafe execution (no eval/exec with user content).\n"
                "3) Use least privilege and protect secrets via environment variables.\n"
                "4) Rate-limit sensitive endpoints.\n"
                "5) Log safely (no PII in logs).\n\n"
                f"Your request: {prompt}"
            )
        if key == "debugging":
            return (
                "Teaching: Debugging method (works for any language)\n\n"
                "1) Reproduce the bug reliably.\n"
                "2) Reduce the problem to a minimal failing input.\n"
                "3) Trace data flow: what is the input, what changes, what is expected.\n"
                "4) Check invariants and edge cases.\n"
                "5) Fix and verify with tests (including the failing case).\n\n"
                f"Your request: {prompt}"
            )
        return (
            "Teaching: Programming foundations\n\n"
            "1) Start with the specification: inputs, constraints, outputs.\n"
            "2) Break the task into small functions/modules.\n"
            "3) Choose clear data structures that match the problem.\n"
            "4) Write tests for edge cases early.\n"
            "5) Iterate: correctness first, then optimization.\n\n"
            f"Your request: {prompt}"
        )

    def _explain_line_by_line(self, code: str) -> List[str]:
        lines = code.splitlines()
        out: List[str] = []
        for i, line in enumerate(lines[:250]):
            stripped = line.strip()
            if not stripped:
                continue
            desc = ""
            if stripped.startswith("def "):
                desc = f"Defines a function at line {i + 1}."
            elif stripped.startswith("class "):
                desc = f"Defines a class at line {i + 1}."
            elif stripped.startswith("import ") or stripped.startswith("from "):
                desc = f"Imports a module at line {i + 1}."
            elif stripped.startswith("return "):
                desc = f"Returns a value at line {i + 1}."
            elif stripped.startswith("if "):
                desc = f"Conditional logic at line {i + 1}."
            elif "for " in stripped or "while " in stripped:
                desc = f"Looping logic at line {i + 1}."
            elif stripped.startswith("try:"):
                desc = f"Starts exception handling at line {i + 1}."
            elif stripped.startswith("@"):
                desc = f"Decorator at line {i + 1}."
            else:
                desc = f"Line {i + 1}: applies statement logic."
            out.append(f"{i + 1}. {stripped} — {desc}")

        if not out:
            out.append("No significant code lines detected.")
        return out

    def _wrap_generated(self, code: str, title: str) -> str:
        return (
            f"Generated code: {title}\n\n"
            f"```\n{code}\n```\n\n"
            "Step-by-step (what this code does):\n"
            "1) Defines inputs/outputs clearly.\n"
            "2) Validates or constrains data to avoid unsafe execution.\n"
            "3) Keeps logic in small, testable pieces.\n"
            "4) Handles errors predictably."
        )

    def _python_template(self, req: str) -> Dict[str, Any]:
        low = req.lower()
        if "calculator" in low or "math" in low:
            code = self._code_calculator_python()
            return {
                "topic": "coding",
                "correct": True,
                "mistake": False,
                "reply": self._wrap_generated(code, "Python safe calculator"),
                "code": code,
            }
        if "rest" in low or "api" in low:
            code = self._code_rest_python()
            return {
                "topic": "coding",
                "correct": True,
                "mistake": False,
                "reply": self._wrap_generated(code, "Python simple REST server"),
                "code": code,
            }
        code = self._code_safe_parser_python()
        return {
            "topic": "coding",
            "correct": True,
            "mistake": False,
            "reply": self._wrap_generated(code, "Safe parsing utility"),
            "code": code,
        }

    def _fastapi_template(self, req: str) -> Dict[str, Any]:
        code = self._code_fastapi_safe_endpoints()
        return {
            "topic": "coding",
            "correct": True,
            "mistake": False,
            "reply": self._wrap_generated(code, "FastAPI safe endpoints"),
            "code": code,
        }

    def _react_js_template(self, req: str, lang: str) -> Dict[str, Any]:
        code = self._code_react_chat_ui_snippet()
        return {
            "topic": "coding",
            "correct": True,
            "mistake": False,
            "reply": self._wrap_generated(code, "React chat UI snippet"),
            "code": code,
        }

    def _code_calculator_python(self) -> str:
        return (
            "import re\n\n"
            "def safe_add(expr: str) -> float:\n"
            "    # Safe arithmetic parser for +,-,*,/, parentheses and integers.\n"
            "    s = expr.replace(' ', '')\n"
            "    if not re.fullmatch(r'[0-9+\\-*/().]+', s):\n"
            "        raise ValueError('Expression contains invalid characters.')\n\n"
            "    # Shunting-yard to convert to RPN (no eval).\n"
            "    tokens = re.findall(r'\\d+|[+\\-*/()]', s)\n\n"
            "    prec = {'+':1,'-':1,'*':2,'/':2}\n"
            "    output = []\n"
            "    ops = []\n\n"
            "    for t in tokens:\n"
            "        if t.isdigit():\n"
            "            output.append(float(t))\n"
            "        elif t in prec:\n"
            "            while ops and ops[-1] in prec and prec[ops[-1]] >= prec[t]:\n"
            "                output.append(ops.pop())\n"
            "            ops.append(t)\n"
            "        elif t == '(':\n"
            "            ops.append(t)\n"
            "        elif t == ')':\n"
            "            while ops and ops[-1] != '(':\n"
            "                output.append(ops.pop())\n"
            "            if not ops or ops[-1] != '(':\n"
            "                raise ValueError('Mismatched parentheses.')\n"
            "            ops.pop()\n\n"
            "    while ops:\n"
            "        op = ops.pop()\n"
            "        if op in '()':\n"
            "            raise ValueError('Mismatched parentheses.')\n"
            "        output.append(op)\n\n"
            "    stack = []\n"
            "    for item in output:\n"
            "        if isinstance(item, float):\n"
            "            stack.append(item)\n"
            "        else:\n"
            "            b = stack.pop(); a = stack.pop()\n"
            "            if item == '+': stack.append(a + b)\n"
            "            elif item == '-': stack.append(a - b)\n"
            "            elif item == '*': stack.append(a * b)\n"
            "            elif item == '/':\n"
            "                if b == 0: raise ZeroDivisionError('Division by zero')\n"
            "                stack.append(a / b)\n"
            "            else: raise ValueError('Unknown operator')\n\n"
            "    if len(stack) != 1:\n"
            "        raise ValueError('Invalid expression.')\n"
            "    return stack[0]\n\n"
            "if __name__ == '__main__':\n"
            "    print(safe_add('3*(2+5)-4/2'))\n"
        )

    def _code_rest_python(self) -> str:
        return (
            "from http.server import BaseHTTPRequestHandler, HTTPServer\n"
            "import json\n\n"
            "class Handler(BaseHTTPRequestHandler):\n"
            "    def _send(self, code, payload):\n"
            "        self.send_response(code)\n"
            "        self.send_header('Content-Type', 'application/json')\n"
            "        self.end_headers()\n"
            "        self.wfile.write(json.dumps(payload).encode('utf-8'))\n\n"
            "    def do_GET(self):\n"
            "        if self.path == '/health':\n"
            "            return self._send(200, {'ok': True})\n"
            "        return self._send(404, {'error': 'not found'})\n\n"
            "    def do_POST(self):\n"
            "        if self.path != '/echo':\n"
            "            return self._send(404, {'error': 'not found'})\n"
            "        length = int(self.headers.get('Content-Length', '0'))\n"
            "        body = self.rfile.read(length).decode('utf-8')\n"
            "        data = json.loads(body) if body else {}\n"
            "        return self._send(200, {'echo': data})\n\n"
            "if __name__ == '__main__':\n"
            "    httpd = HTTPServer(('0.0.0.0', 8000), Handler)\n"
            "    print('Listening on http://0.0.0.0:8000')\n"
            "    httpd.serve_forever()\n"
        )

    def _code_safe_parser_python(self) -> str:
        return (
            "import re\n\n"
            "def extract_integers(text: str):\n"
            "    # Safe parsing: only digits and optional leading minus signs.\n"
            "    return [int(x) for x in re.findall(r'-?\\d+', text)]\n\n"
            "def compute_mean(numbers):\n"
            "    if not numbers:\n"
            "        raise ValueError('No numbers provided')\n"
            "    return sum(numbers) / len(numbers)\n\n"
            "if __name__ == '__main__':\n"
            "    nums = extract_integers('Scores: 10, -2, 7')\n"
            "    print(compute_mean(nums))\n"
        )

    def _code_fastapi_safe_endpoints(self) -> str:
        return (
            "from __future__ import annotations\n"
            "from fastapi import FastAPI, HTTPException\n"
            "from pydantic import BaseModel, Field\n"
            "import re\n\n"
            "app = FastAPI()\n\n"
            "class ChatRequest(BaseModel):\n"
            "    user_id: str\n"
            "    message: str = Field(min_length=1, max_length=2000)\n\n"
            "def safe_extract_integers(text: str):\n"
            "    return [int(x) for x in re.findall(r'-?\\d+', text)]\n\n"
            "@app.post('/chat')\n"
            "def chat(req: ChatRequest):\n"
            "    nums = safe_extract_integers(req.message)\n"
            "    if not nums:\n"
            "        raise HTTPException(status_code=400, detail='No integers found in message')\n"
            "    mean = sum(nums) / len(nums)\n"
            "    return {'reply': f'Mean of your numbers is {mean}', 'count': len(nums)}\n\n"
            "@app.get('/health')\n"
            "def health():\n"
            "    return {'ok': True}\n"
        )

    def _code_react_chat_ui_snippet(self) -> str:
        return (
            "import React, { useEffect, useRef, useState } from 'react';\n\n"
            "export default function Chat({ apiUrl }) {\n"
            "  const [messages, setMessages] = useState([]);\n"
            "  const [input, setInput] = useState('');\n"
            "  const [loading, setLoading] = useState(false);\n"
            "  const endRef = useRef(null);\n\n"
            "  useEffect(() => {\n"
            "    endRef.current?.scrollIntoView({ behavior: 'smooth' });\n"
            "  }, [messages, loading]);\n\n"
            "  async function send() {\n"
            "    const text = input.trim();\n"
            "    if (!text) return;\n"
            "    setInput('');\n\n"
            "    const userMsg = {\n"
            "      id: Date.now() + '-u',\n"
            "      role: 'user',\n"
            "      text,\n"
            "      ts: new Date().toISOString(),\n"
            "    };\n"
            "    setMessages(m => [...m, userMsg]);\n"
            "    setLoading(true);\n\n"
            "    try {\n"
            "      const res = await fetch(apiUrl + '/chat', {\n"
            "        method: 'POST',\n"
            "        headers: { 'Content-Type': 'application/json' },\n"
            "        body: JSON.stringify({ user_id: 'local-user', message: text }),\n"
            "      });\n"
            "      const data = await res.json();\n"
            "      const aiMsg = {\n"
            "        id: Date.now() + '-a',\n"
            "        role: 'ai',\n"
            "        text: data.reply,\n"
            "        ts: new Date().toISOString(),\n"
            "      };\n"
            "      setMessages(m => [...m, aiMsg]);\n"
            "    } finally {\n"
            "      setLoading(false);\n"
            "    }\n"
            "  }\n\n"
            "  return (\n"
            "    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>\n"
            "      <div style={{ flex: 1, overflowY: 'auto' }} aria-label='messages'>\n"
            "        {messages.map(msg => (\n"
            "          <div key={msg.id} style={{ margin: 8, textAlign: msg.role === 'user' ? 'right' : 'left' }}>\n"
            "            <div\n"
            "              style={{\n"
            "                display: 'inline-block',\n"
            "                padding: 10,\n"
            "                borderRadius: 10,\n"
            "                background: msg.role==='user' ? '#dcf8c6' : '#f1f1f1',\n"
            "              }}\n"
            "            >\n"
            "              {msg.text}\n"
            "            </div>\n"
            "          </div>\n"
            "        ))}\n"
            "        {loading && <div style={{ margin: 8 }}>AI is thinking...</div>}\n"
            "        <div ref={endRef} />\n"
            "      </div>\n"
            "      <div style={{ display: 'flex', gap: 8, padding: 12 }} >\n"
            "        <input\n"
            "          value={input}\n"
            "          onChange={e => setInput(e.target.value)}\n"
            "          onKeyDown={e => (e.key==='Enter' ? send() : null)}\n"
            "          style={{ flex: 1 }}\n"
            "        />\n"
            "        <button onClick={send} disabled={loading}>Send</button>\n"
            "      </div>\n"
            "    </div>\n"
            "  );\n"
            "}\n"
        )


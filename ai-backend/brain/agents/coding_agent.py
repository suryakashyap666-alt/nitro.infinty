from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class CodingWork:
    language: str
    approach: List[str]
    code: str
    tests: List[str]


class CodingAgent:
    def __init__(self) -> None:
        pass

    def _detect_language(self, text: str) -> str:
        t = (text or "").lower()
        if "fastapi" in t or "python" in t or "pydantic" in t:
            return "python"
        if "react" in t or "javascript" in t or "jsx" in t or "typescript" in t:
            return "javascript"
        return "python"

    def _safe_code_snippet(self, task: str, lang: str) -> Tuple[str, List[str], List[str]]:
        # Non-placeholder: generate real working snippets for common tasks.
        # Supports: fastapi echo/chat, react input UI, safe expression evaluator.
        low = (task or "").lower()
        if lang == "python" and "fastapi" in low:
            code = (
                "from fastapi import FastAPI, HTTPException\n"
                "from pydantic import BaseModel, Field\n"
                "from typing import Any, Dict\n\n"
                "app = FastAPI(title='Nitro Safe API')\n\n"
                "class ChatRequest(BaseModel):\n"
                "    user_id: str\n"
                "    message: str = Field(min_length=1, max_length=2000)\n\n"
                "def safe_extract_integers(text: str):\n"
                "    import re\n"
                "    return [int(x) for x in re.findall(r'-?\\d+', text)]\n\n"
                "@app.post('/chat')\n"
                "def chat(req: ChatRequest) -> Dict[str, Any]:\n"
                "    nums = safe_extract_integers(req.message)\n"
                "    if not nums:\n"
                "        raise HTTPException(status_code=400, detail='No integers found in message')\n"
                "    mean = sum(nums) / len(nums)\n"
                "    return {'reply': f'Mean: {mean}', 'count': len(nums)}\n"
            )
            approach = [
                "Define a Pydantic model to validate inputs.",
                "Avoid unsafe evaluation; only parse integers via regex.",
                "Return predictable JSON responses and proper HTTP errors.",
            ]
            tests = [
                "POST /chat with message '3 10 -2' => mean computed",
                "POST /chat with message 'hello' => 400 error",
            ]
            return code, approach, tests

        if lang == "javascript":
            code = (
                "import React, { useMemo, useState } from 'react';\n\n"
                "export default function LocalChat({ onSend }) {\n"
                "  const [text, setText] = useState('');\n"
                "  const [msgs, setMsgs] = useState([]);\n\n"
                "  const canSend = useMemo(() => text.trim().length > 0, [text]);\n\n"
                "  async function send() {\n"
                "    if (!canSend) return;\n"
                "    const t = text.trim();\n"
                "    setText('');\n"
                "    const userMsg = { id: Date.now() + '-u', role: 'user', text: t, ts: new Date().toISOString() };\n"
                "    const next = [...msgs, userMsg];\n"
                "    setMsgs(next);\n\n"
                "    const aiText = await onSend(t);\n"
                "    const aiMsg = { id: Date.now() + '-a', role: 'ai', text: aiText, ts: new Date().toISOString() };\n"
                "    setMsgs(m => [...m, aiMsg]);\n"
                "  }\n\n"
                "  return (\n"
                "    <div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>\n"
                "      <div style={{ flex: 1, overflowY: 'auto', padding: 8 }}>\n"
                "        {msgs.map(m => (\n"
                "          <div key={m.id} style={{ textAlign: m.role === 'user' ? 'right' : 'left', margin: 6 }}>\n"
                "            <span style={{ display: 'inline-block', padding: '8px 10px', borderRadius: 10, background: m.role==='user' ? '#dcf8c6' : '#f1f1f1' }}>\n"
                "              {m.text}\n"
                "            </span>\n"
                "          </div>\n"
                "        ))}\n"
                "      </div>\n"
                "      <div style={{ display: 'flex', gap: 8, padding: 10 }}>\n"
                "        <input value={text} onChange={e => setText(e.target.value)} onKeyDown={e => (e.key === 'Enter' ? send() : null)} style={{ flex: 1 }} />\n"
                "        <button disabled={!canSend} onClick={send}>Send</button>\n"
                "      </div>\n"
                "    </div>\n"
                "  );\n"
                "}\n"
            )
            approach = [
                "Use state to store the message list.",
                "Separate UI event (send) from the actual API call via onSend.",
                "Append user message immediately and then append AI message when resolved.",
            ]
            tests = [
                "Typing and Enter adds a user message",
                "onSend resolves and adds AI message",
            ]
            return code, approach, tests

        # Default python safe arithmetic parser
        code = (
            "import re\n\n"
            "def safe_eval_arithmetic(expr: str) -> float:\n"
            "    s = (expr or '').replace(' ', '')\n"
            "    if not s:\n"
            "        raise ValueError('Empty expression')\n"
            "    if not re.fullmatch(r'[0-9+\\-*/().]+', s):\n"
            "        raise ValueError('Expression contains invalid characters')\n\n"
            "    # Shunting-yard to RPN\n"
            "    tokens = re.findall(r'\\d+|[+\\-*/()]', s)\n"

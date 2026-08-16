from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


_ALLOWED_CREATE_BOT_INTENTS = {
    "coding",
    "bot creation",
    "ui mockup",
    "reasoning",
    "feature planning",
}


def _is_unrelated_request(text: str) -> bool:
    t = (text or "").lower()
    related_markers = [
        "bot",
        "marketplace",
        "skill",
        "category",
        "icon",
        "ratings",
        "description",
        "create",
        "ui",
        "mock",
        "features",
        "plan",
        "coding",
        "reasoning",
        "logic",
        "data structure",
        "api",
        "frontend",
        "backend",
        "profession",
        "career",
        "workflow",
        "tools",
        "mentor",
        "training",
        "healthcare",
        "engineer",
        "designer",
        "teacher",
        "lawyer",
        "accountant",
    ]

    unrelated_markers = [
        "solve",
        "calculate",
        "equation",
        "integral",
        "derivative",
        "trigonometry",
        "algebra",
        "geometry",
        "geometry problem",
        "math",
        "random chat",
        "tell me a joke",
        "weather",
    ]

    if any(u in t for u in unrelated_markers):
        return True

    # If it has no obvious bot-building/coding markers, treat as unrelated.
    return not any(m in t for m in related_markers)


def _extract_category_from_text(text: str) -> Optional[str]:
    t = (text or "").lower()
    # Lightweight heuristics
    if "math" in t:
        return "math"
    if "coding" in t or "code" in t or "program" in t:
        return "coding"
    if "emotional" in t or "feel" in t or "support" in t:
        return "emotional"
    if "exam" in t or "iit" in t or "cbse" in t:
        return "exam"
    if "reason" in t or "logic" in t:
        return "reasoning"
    if "career" in t or "profession" in t or "workflow" in t:
        return "profession"
    if "designer" in t or "artist" in t or "writer" in t:
        return "creative"
    if "engineer" in t or "technician" in t or "scientist" in t:
        return "engineering"
    return None


def _parse_skills_lines(text: str) -> List[str]:
    # Accept formats like:
    # - skill1
    # - skill2
    lines = []
    for raw in (text or "").splitlines():
        line = raw.strip()
        if not line:
            continue
        m = re.match(r"^[-*•]\s*(.+)$", line)
        if m:
            lines.append(m.group(1).strip())
            continue
        if "," in line and "skill" in line.lower():
            parts = [p.strip() for p in line.split(":", 1)[-1].split(",")]
            lines.extend([p for p in parts if p])
    return [s for s in lines if s][:12]


def _ensure_bot_shape(state: Dict[str, Any]) -> Dict[str, Any]:
    state = dict(state or {})
    state.setdefault("name", "")
    state.setdefault("description", "")
    state.setdefault("skills", [])
    state.setdefault("ratings", 0.0)
    state.setdefault("creator", "")
    state.setdefault("category", "")
    state.setdefault("icon", "🤖")
    return state


def create_bot_reply(user_text: str, creator: str, conversation_state: Dict[str, Any]) -> Dict[str, Any]:
    """Return {reply, done, botDraft}.

    - Enforces strict related-only behavior.
    - Updates draft bot fields based on conversation heuristics.
    """

    state = _ensure_bot_shape(conversation_state)

    if (user_text or "").strip().lower() == "the ai is now done":
        done = True
        # Ensure minimal required fields
        name = (state.get("name") or "").strip() or "Custom Bot"
        description = (state.get("description") or "").strip() or "A custom AI bot created in Nitro Infinity AI."
        skills = state.get("skills") or []
        if not skills:
            skills = [
                "coding",
                "reasoning",
                "feature planning",
            ]

        category = (state.get("category") or "").strip() or _extract_category_from_text(description) or "coding"
        icon = (state.get("icon") or "").strip() or "✨"

        botDraft = {
            "name": name,
            "description": description,
            "skills": skills,
            "ratings": float(state.get("ratings") or 4.5),
            "creator": (state.get("creator") or creator or "Nitro Infinity AI"),
            "category": category,
            "icon": icon,
        }

        reply = (
            "Finalizing your bot. Saving to the Bots Marketplace now.\n\n"
            "If you want any last tweaks, say what to change before finalizing again."
        )
        return {"reply": reply, "done": done, "botDraft": botDraft}

    if _is_unrelated_request(user_text):
        return {
            "reply": "Here I only allow coding, reasoning, bot creation, and UI planning tasks.",
            "done": False,
            "botDraft": state,
        }

    done = False

    # Heuristic extraction
    t = (user_text or "").strip()
    lower = t.lower()

    # name suggestion
    m_name = re.search(r"name\s*[:=]\s*([^\n]+)", t, flags=re.IGNORECASE)
    if m_name:
        state["name"] = m_name.group(1).strip()[:40]

    if "description" in lower and ":" in t:
        parts = t.split(":", 1)
        if len(parts) == 2:
            state["description"] = parts[1].strip()[:240]

    # skills
    skills_from_lines = _parse_skills_lines(t)
    if skills_from_lines:
        state["skills"] = skills_from_lines

    # category / icon
    cat = _extract_category_from_text(t)
    if cat:
        state["category"] = cat

    if any(sym in t for sym in ["🧠", "🤖", "✨", "🧮", "⚡", "🎯", "📚"]):
        # pick first icon-like emoji
        for ch in t:
            if ch in "🧠🤖✨🧮⚡🎯📚":
                state["icon"] = ch
                break

    if not state.get("creator"):
        state["creator"] = creator

    # Ask clarifying question to guide construction
    missing = []
    if not (state.get("name") or "").strip():
        missing.append("a bot name")
    if not (state.get("description") or "").strip():
        missing.append("a short description")
    if not (state.get("skills") or []):
        missing.append("a skills list")

    if missing:
        reply = (
            "Got it. I can help you build this bot.\n\n"
            f"To continue, please provide: {', '.join(missing)}.\n"
            "Tip: You can write like this:\n"
            "- Name: <bot name>\n"
            "- Description: <what it does>\n"
            "- Skills: <comma separated or bullet list>\n"
            "\nWhen you're finished, say: The AI is now done"
        )
    else:
        # Confirmation summary
        reply = (
            "Nice. I’ve updated your bot draft.\n\n"
            f"Draft name: {state.get('name')}\n"
            f"Category: {state.get('category')}\n"
            f"Skills: {', '.join(state.get('skills') or [])}\n\n"
            "Send more details or say: The AI is now done"
        )

    return {"reply": reply, "done": done, "botDraft": state}


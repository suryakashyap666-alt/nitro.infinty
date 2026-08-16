from __future__ import annotations

import base64
import hashlib
import json
import re
from dataclasses import dataclass
from typing import Any, Callable, Dict, Optional, Tuple

from ..brain.response_composer import ResponseComposer
from ..education.subjects import detect_subject_id
from .puzzle_learning_store import GlobalPuzzleLearningStore





@dataclass(frozen=True)
class PuzzleResult:
    recognized: bool
    puzzle_type: str
    reply: str
    final_answer: Optional[str] = None
    steps: Optional[list[str]] = None
    solving_trick: Optional[str] = None
    reasoning_path: Optional[list[str]] = None
    hint_logic: Optional[str] = None


class PuzzleDetector:
    """Best-effort rule detector for puzzle types.

    Full image/OCR solving is not available in this lite repo; we support:
    - text instruction puzzles
    - placeholder image hashing + type guessing

    The goal is: recognize enough to trigger memory lookup and provide
    educational step-by-step reasoning.
    """

    TYPE_KEYWORDS: Dict[str, Tuple[str, ...]] = {
        # word puzzles
        "crossword": ("crossword", "across", "down"),
        "word_search": ("word search", "wordsearch", "find the words"),
        "anagram": ("anagram", "scramble"),
        "word_ladder": ("word ladder", "transform"),
        "cryptogram": ("cryptogram", "substitution cipher"),

        # number / logic
        "sudoku": ("sudoku", "9x9"),
        "logic_grid": ("logic grid", "logic puzzle"),
        "kakuro": ("kakuro", "kakuro puzzle"),
        "kenken": ("kenken", "ken ken"),

        # spatial/object
        "sliding_tile": ("sliding", "15-puzzle", "15 puzzle", "sliding tile"),
        "tangram": ("tangram",),
        "jigsaw": ("jigsaw", "jigsaw puzzle"),
        "rubiks": ("rubik", "rubik's"),

        # visual
        "spot_difference": ("spot the difference", "differences"),
        "maze": ("maze", "labyrinth"),

        # mystery
        "riddle": ("riddle", "riddles"),
        "escape_room": ("escape room", "escape-room"),
        "murder_mystery": ("murder mystery", "murder"),
        "arg": ("alternate reality", "arg"),
    }

    def detect_from_text(self, text: str) -> Tuple[bool, str]:
        t = (text or "").lower()
        if not t.strip():
            return False, "unknown"
        for ptype, keys in self.TYPE_KEYWORDS.items():
            if any(k in t for k in keys):
                return True, ptype

        # generic sudoku-like hints
        if re.search(r"\b(\d\s*){81}\b", t.replace("\n", " ")):
            return True, "sudoku"

        return False, "unknown"

    def detect_from_message(self, message: str) -> Tuple[bool, str]:
        return self.detect_from_text(message)


class PuzzleMemory:
    """Global shared memory (across all users) for puzzle learning.

    Stored inside backend/data/nitro_state.json under a `puzzle_learning` key.
    """

    def __init__(self, storage_path: str) -> None:
        self.storage_path = storage_path
        self._ensure()

    def _ensure(self) -> None:
        import os

        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            data = {}

        if not isinstance(data, dict):
            data = {}
        data.setdefault("puzzle_learning", {})
        tmp = self.storage_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.storage_path)

    def _load(self) -> Dict[str, Any]:
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                return {}
            data.setdefault("puzzle_learning", {})
            return data
        except Exception:
            return {"puzzle_learning": {}}

    def _save(self, data: Dict[str, Any]) -> None:
        import os

        tmp = self.storage_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.storage_path)

    def _hash_payload(self, *, puzzle_type: str, text: str, image_b64: Optional[str]) -> str:
        h = hashlib.sha256()
        h.update(puzzle_type.encode("utf-8"))
        h.update(b"\0")
        h.update((text or "").encode("utf-8"))
        if image_b64:
            h.update(b"\0")
            # image_b64 may be huge; for speed, hash only first N chars
            h.update(image_b64[:5000].encode("utf-8"))
        return h.hexdigest()

    def lookup(self, *, puzzle_type: str, text: str, image_b64: Optional[str]) -> Optional[Dict[str, Any]]:
        data = self._load()
        pl = data.get("puzzle_learning") or {}
        key = self._hash_payload(puzzle_type=puzzle_type, text=text, image_b64=image_b64)
        entry = pl.get(key)
        return entry if isinstance(entry, dict) else None

    def store(
        self,
        *,
        puzzle_type: str,
        text: str,
        image_b64: Optional[str],
        payload: Dict[str, Any],
    ) -> str:
        data = self._load()
        pl = data.setdefault("puzzle_learning", {})
        key = self._hash_payload(puzzle_type=puzzle_type, text=text, image_b64=image_b64)
        pl[key] = payload
        self._save(data)
        return key


class PuzzleEngine:
    def __init__(self, storage_path: str) -> None:
        self.detector = PuzzleDetector()
        self.memory = PuzzleMemory(storage_path=storage_path)
        self.composer = ResponseComposer()

    def _extract_answer_intent(self, message: str) -> str:
        lower = (message or "").lower()
        if "hint" in lower:
            return "hint"
        if "solve" in lower or "answer" in lower:
            return "answer"
        return "answer"

    def solve(
        self,
        *,
        user_id: str,
        message: str,
        bot_education_enabled: bool,
        image_b64: Optional[str] = None,
        hint_mode: Optional[str] = None,
        progress_callback: Callable[[int], None] | None = None,
    ) -> PuzzleResult:
        # bot gating handled by caller; engine still runs.
        def _progress(value: int) -> None:
            if progress_callback is None:
                return
            try:
                progress_callback(max(0, min(100, int(value))))
            except Exception:
                pass

        _progress(10)
        hint_mode = hint_mode or self._extract_answer_intent(message)

        recognized, ptype = self.detector.detect_from_message(message)
        if not recognized:
            # still try: use subjects as a fallback heuristic for reasoning direction
            subj = detect_subject_id(message, fallback="mathematics")
            ptype = f"unknown_{subj}" if subj else "unknown"

        # memory lookup (exact)
        mem = self.memory.lookup(puzzle_type=ptype, text=message, image_b64=image_b64)
        if not mem:
            # similarity lookup across global shared memory
            global_store = GlobalPuzzleLearningStore(storage_path=self.memory.storage_path)
            best = global_store.find_similar(query_text=message, puzzle_type=ptype)
            mem = best.entry if best else None
        if mem:
            _progress(60)

            final_answer = mem.get("final_answer")
            steps = mem.get("steps")
            solving_trick = mem.get("solving_trick")
            reply = "I found this puzzle in my shared memory.\n\n"
            if hint_mode == "hint" and mem.get("hint_logic"):
                reply += f"Hint: {mem.get('hint_logic')}\n"
            else:
                if final_answer:
                    reply += f"Final Answer: {final_answer}\n"
                if steps:
                    reply += "\nStep-by-step:\n" + "\n".join([f"{i+1}) {s}" for i, s in enumerate(steps[:12])])
            if solving_trick:
                reply += "\n\nShortcut/Trick: " + str(solving_trick)
            return PuzzleResult(
                recognized=True,
                puzzle_type=mem.get("puzzle_type", ptype),
                reply=reply.strip(),
                final_answer=final_answer,
                steps=steps,
                solving_trick=solving_trick,
                reasoning_path=mem.get("reasoning_path"),
                hint_logic=mem.get("hint_logic"),
            )

        # failsafe solver
        if not bot_education_enabled:
            return PuzzleResult(
                recognized=False,
                puzzle_type=ptype,
                reply="Puzzle solving is disabled for this bot until educationEnabled is enabled.",
                final_answer=None,
                steps=None,
                hint_logic=None,
            )

        if hint_mode == "hint":
            hint = "Tell me the key constraint/rules (size, symbols/letters, or win condition). Then I’ll deduce the next step." \
                if ptype.startswith("unknown") else "I’ll give a hint first. Provide any missing grid/letters so I can proceed." 
            reply = f"{hint}\n\nI’m still learning, but I can still attempt deduction step-by-step."
            # store partial learning if user asked for hint
            entry = {
                "puzzle_type": ptype,
                "text": message,
                "image_provided": bool(image_b64),
                "solving_trick": None,
                "solving_pattern": None,
                "reasoning_path": ["hint_requested"],
                "hint_logic": hint,
                "reverse_engineered_logic": None,
                "full_explanation": None,
                "final_answer": None,
                "steps": None,
                "user_learning": "partial_hint",
            }
            self.memory.store(
                puzzle_type=ptype,
                text=message,
                image_b64=image_b64,
                payload=entry,
            )
            return PuzzleResult(
                recognized=bool(recognized),
                puzzle_type=ptype,
                reply=reply,
                final_answer=None,
                steps=None,
                hint_logic=hint,
            )

        # attempt a generic step-by-step reasoning reconstruction
        steps = [
            "Identify the puzzle type and rules from the text/grid.",
            "Extract constraints (dimensions, symbols, allowed moves, or target condition).",
            "Convert the puzzle into a small state (variables + constraints).",
            "Apply deduction: narrow possibilities using constraints.",
            "If still stuck, use a structured search/backtracking plan.",
        ]
        reply = (
            "I can’t fully solve this yet, but I can attempt it step-by-step.\n\n"
            + "Step-by-step plan:\n" + "\n".join([f"{i+1}) {s}" for i, s in enumerate(steps)])
            + "\n\nSend the exact grid/letters (or upload the screenshot again) and I’ll try deeper deduction."
        )

        entry = {
            "puzzle_type": ptype,
            "text": message,
            "image_provided": bool(image_b64),
            "solving_trick": None,
            "solving_pattern": "generic_constraint_deduction",
            "reasoning_path": ["generic_attempt"],
            "hint_logic": "Share the full grid/rules to enable exact solving.",
            "reverse_engineered_logic": None,
            "full_explanation": reply,
            "final_answer": None,
            "steps": steps,
            "user_learning": "attempt",
        }
        self.memory.store(puzzle_type=ptype, text=message, image_b64=image_b64, payload=entry)

        _progress(100)
        return PuzzleResult(
            recognized=bool(recognized),
            puzzle_type=ptype,
            reply=reply.strip(),
            final_answer=None,
            steps=steps,
            reasoning_path=entry.get("reasoning_path"),
            hint_logic=entry.get("hint_logic"),
        )


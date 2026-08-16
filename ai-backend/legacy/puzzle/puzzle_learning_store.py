from __future__ import annotations

import json
import os
from dataclasses import dataclass
from typing import Any, Dict, Optional

from .puzzle_similarity import similarity_score


@dataclass
class PuzzleLearningMatch:
    key: str
    score: float
    entry: Dict[str, Any]


class GlobalPuzzleLearningStore:
    """Global shared puzzle learning helper.

    Uses backend/data/nitro_state.json (same as PuzzleMemory) but adds similarity matching.
    """

    def __init__(self, storage_path: str) -> None:
        self.storage_path = storage_path
        self._ensure()

    def _ensure(self) -> None:
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        if not os.path.exists(self.storage_path):
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump({"puzzle_learning": {}}, f, ensure_ascii=False, indent=2)

    def _load(self) -> Dict[str, Any]:
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, dict):
                data = {}
            data.setdefault("puzzle_learning", {})
            return data
        except Exception:
            return {"puzzle_learning": {}}

    def find_similar(
        self,
        *,
        query_text: str,
        puzzle_type: str,
        min_score: float = 0.55,
        max_results: int = 5,
    ) -> Optional[PuzzleLearningMatch]:
        data = self._load()
        pl = data.get("puzzle_learning") or {}
        best: Optional[PuzzleLearningMatch] = None

        for key, entry in pl.items():
            if not isinstance(entry, dict):
                continue
            if str(entry.get("puzzle_type") or "") != str(puzzle_type):
                continue

            cand_text = str(entry.get("text") or "")
            score = similarity_score(query_text, cand_text)
            if score < min_score:
                continue

            if best is None or score > best.score:
                best = PuzzleLearningMatch(key=key, score=score, entry=entry)

        return best


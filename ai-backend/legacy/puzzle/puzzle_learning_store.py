from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional
from .puzzle_similarity import similarity_score


class GlobalPuzzleLearningStore:
    def __init__(self, storage_path: str) -> None:
        self.storage_path = storage_path

    def _load(self) -> Dict[str, Any]:
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"puzzle_learning": {}}

    def find_similar(self, *, query_text: str, puzzle_type: str, min_score: float = 0.55) -> Optional[Dict[str, Any]]:
        data = self._load()
        pl = data.get("puzzle_learning") or {}
        for key, entry in pl.items():
            if str(entry.get("puzzle_type") or "") == str(puzzle_type):
                if similarity_score(query_text, str(entry.get("text") or "")) >= min_score:
                    return entry
        return None
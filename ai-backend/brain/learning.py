from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

DIFFICULTIES = ["easy", "medium", "hard"]
STYLE_WEAK_PROBING = "probe"
STYLE_STEP_BY_STEP = "steps"
STYLE_MIXED = "mixed"


@dataclass
class SubjectLearningState:
    correct_answers: int = 0
    total_attempts: int = 0
    learning_style: str = STYLE_MIXED
    learning_speed_ema: float = 0.5
    weak_score: int = 0
    strong_score: int = 0
    difficulty_idx: int = 1
    streak: int = 0
    history: List[Dict[str, Any]] = None

    def __post_init__(self) -> None:
        if self.history is None:
            self.history = []


@dataclass
class UserLearningState:
    subjects: Dict[str, SubjectLearningState] = None

    def __post_init__(self) -> None:
        if self.subjects is None:
            self.subjects = {}


class LearningEngine:
    """Adaptive learning engine: updates difficulty, tracks mastery and weak topics."""

    def __init__(self, storage_path: str) -> None:
        self.storage_path = storage_path
        self._ensure_storage()

    def _ensure_storage(self) -> None:
        os.makedirs(os.path.dirname(self.storage_path), exist_ok=True)
        if not os.path.exists(self.storage_path):
            with open(self.storage_path, "w", encoding="utf-8") as f:
                json.dump({"users": {}}, f)

    def _load(self) -> Dict[str, Any]:
        try:
            with open(self.storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {"users": {}}

    def _save(self, data: Dict[str, Any]) -> None:
        tmp = self.storage_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp, self.storage_path)

    def get_or_init_user(self, user_id: str) -> UserLearningState:
        data = self._load()
        users = data.setdefault("users", {})
        u = users.setdefault(user_id, {})
        l = u.get("learning")
        if not l or not isinstance(l, dict):
            u["learning"] = asdict(UserLearningState())
            return UserLearningState()

        raw_subjects = l.get("subjects") or {}
        subjects_dict: Dict[str, SubjectLearningState] = {}
        for sid, sdata in raw_subjects.items():
            if isinstance(sdata, dict):
                subjects_dict[sid] = SubjectLearningState(**sdata)
            elif isinstance(sdata, SubjectLearningState):
                subjects_dict[sid] = sdata

        return UserLearningState(subjects=subjects_dict)

    def _persist(self, user_id: str, state: UserLearningState) -> None:
        data = self._load()
        users = data.setdefault("users", {})
        users.setdefault(user_id, {})["learning"] = asdict(state)
        self._save(data)

    def update_subject_from_quiz(
        self,
        user_id: str,
        *,
        subject_id: str,
        is_correct: bool,
        learning_time_s: Optional[float] = None,
    ) -> None:
        user = self.get_or_init_user(user_id)
        sid = str(subject_id)

        if sid not in user.subjects:
            user.subjects[sid] = SubjectLearningState()

        st = user.subjects[sid]
        st.total_attempts += 1
        if is_correct:
            st.correct_answers += 1
            st.strong_score += 1
            st.streak += 1
        else:
            st.weak_score += 1
            st.streak = 0

        if st.streak >= 3 and st.difficulty_idx < 2:
            st.difficulty_idx += 1
            st.streak = 0
        elif (not is_correct) and st.difficulty_idx > 0:
            st.difficulty_idx -= 1

        speed_signal = 1.0 if is_correct else 0.2
        st.learning_speed_ema = (0.85 * st.learning_speed_ema) + (
            0.15 * speed_signal * (1.0 + min(2.0, st.streak / 3.0))
        )
        st.learning_style = STYLE_WEAK_PROBING if is_correct else STYLE_STEP_BY_STEP

        st.history.append({
            "subject_id": sid,
            "correct": is_correct,
            "difficulty": DIFFICULTIES[min(st.difficulty_idx, len(DIFFICULTIES) - 1)],
        })

        self._persist(user_id, user)

    def update_from_math(self, user_id: str, result: Dict[str, Any]) -> None:
        topic = result.get("topic", "algebra")
        is_correct = bool(result.get("correct", False))
        self.update_subject_from_quiz(user_id, subject_id=topic, is_correct=is_correct)

    def get_weak_subjects(self, user_id: str, threshold: float = 0.55) -> List[str]:
        user = self.get_or_init_user(user_id)
        weak = []
        for sid, st in user.subjects.items():
            if st.total_attempts > 0:
                if (st.correct_answers / st.total_attempts) < threshold:
                    weak.append(sid)
        return weak

    def get_learning_profile(self, user_id: str) -> Dict[str, Any]:
        user = self.get_or_init_user(user_id)
        total_attempts = sum(st.total_attempts for st in user.subjects.values())
        total_correct = sum(st.correct_answers for st in user.subjects.values())
        overall_success = (total_correct / max(1, total_attempts)) if total_attempts > 0 else 0.0

        return {
            "total_attempts": total_attempts,
            "total_correct": total_correct,
            "overall_success_rate": overall_success,
            "weak_subjects": self.get_weak_subjects(user_id),
        }
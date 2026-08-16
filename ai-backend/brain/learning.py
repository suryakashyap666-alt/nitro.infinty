from __future__ import annotations

import json
import os
import random
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional

try:
    from legacy.education.subjects import SUBJECTS
except (ImportError, ValueError):
    try:
        from education.subjects import SUBJECTS
    except (ImportError, ValueError):
        SUBJECTS = {}

TOPICS: List[str] = []
DIFFICULTIES = ["easy", "medium", "hard"]
QUESTION_STYLES = ["IIT", "CBSE"]

DEFAULT_DIFFICULTY = "medium"

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
    """Adaptive learning: updates difficulty and selects weak topics."""

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

    def decide_next_action(self, user_id: str, topic_hint: str) -> Dict[str, Any]:
        user = self.get_or_init_user(user_id)
        subject_id = str(topic_hint)

        subj = user.subjects.get(subject_id)
        if subj is None:
            subj = SubjectLearningState()
            user.subjects[subject_id] = subj
            self._persist(user_id, user)

        difficulty = (
            DIFFICULTIES[subj.difficulty_idx]
            if 0 <= subj.difficulty_idx < len(DIFFICULTIES)
            else DIFFICULTIES[1]
        )
        total = max(1, subj.total_attempts)
        success_rate = subj.correct_answers / total

        weak_topics = [topic_hint] if success_rate < 0.55 else []
        chosen = topic_hint

        if chosen == "computer_science":
            return {
                "type": "coding",
                "prompt": self._coding_prompt(user_id, subj, chosen),
                "weak_topics": weak_topics[:5],
                "streak": subj.streak,
                "difficulty": difficulty,
                "strict": True,
            }

        if chosen in {"mathematics", "science", "social_science"}:
            return {
                "type": "math",
                "prompt": self._math_prompt(user_id, subj, chosen),
                "weak_topics": weak_topics[:5],
                "streak": subj.streak,
                "difficulty": difficulty,
                "strict": True,
            }

        return {
            "type": "general",
            "prompt": "general",
            "weak_topics": weak_topics[:5],
            "streak": subj.streak,
            "difficulty": difficulty,
            "strict": True,
        }

    def _math_prompt(self, user_id: str, subj: SubjectLearningState, topic: str) -> str:
        diff_idx = min(max(0, subj.difficulty_idx), len(DIFFICULTIES) - 1)
        return f"Topic:{topic};Difficulty:{DIFFICULTIES[diff_idx]};Practice:adaptive;User:{user_id}"

    def _coding_prompt(self, user_id: str, subj: SubjectLearningState, topic: str) -> str:
        diff_idx = min(max(0, subj.difficulty_idx), len(DIFFICULTIES) - 1)
        return f"Topic:{topic};Difficulty:{DIFFICULTIES[diff_idx]};Practice:adaptive;User:{user_id}"

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

        if learning_time_s is not None and learning_time_s > 0:
            speed_signal = max(0.0, min(1.0, 1.0 / learning_time_s))
        else:
            speed_signal = 1.0 if is_correct else 0.2

        st.learning_speed_ema = (0.85 * st.learning_speed_ema) + (
            0.15 * speed_signal * (1.0 + min(2.0, st.streak / 3.0))
        )

        if is_correct:
            if st.streak >= 2:
                st.learning_style = STYLE_WEAK_PROBING
        else:
            st.learning_style = STYLE_STEP_BY_STEP

        st.history.append(
            {
                "subject_id": sid,
                "kind": "quiz",
                "correct": is_correct,
                "learning_time_s": learning_time_s,
                "learning_style": st.learning_style,
                "speed_ema": st.learning_speed_ema,
                "difficulty": DIFFICULTIES[min(st.difficulty_idx, len(DIFFICULTIES) - 1)],
            }
        )

        self._persist(user_id, user)

    def update_subject_from_worksheet(
        self,
        user_id: str,
        *,
        subject_id: str,
        correct_fraction: float,
    ) -> None:
        correct_fraction = max(0.0, min(1.0, float(correct_fraction)))
        is_correct = correct_fraction >= 0.6
        sid = str(subject_id)

        user = self.get_or_init_user(user_id)
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

        speed_signal = correct_fraction
        st.learning_speed_ema = (0.85 * st.learning_speed_ema) + (
            0.15 * speed_signal * (1.0 + min(2.0, st.streak / 3.0))
        )

        if is_correct:
            if st.streak >= 2:
                st.learning_style = STYLE_WEAK_PROBING
        else:
            st.learning_style = STYLE_STEP_BY_STEP

        st.history.append(
            {
                "subject_id": sid,
                "kind": "worksheet",
                "correct_fraction": correct_fraction,
                "learning_style": st.learning_style,
                "speed_ema": st.learning_speed_ema,
                "difficulty": DIFFICULTIES[min(st.difficulty_idx, len(DIFFICULTIES) - 1)],
            }
        )

        self._persist(user_id, user)

    def update_from_math(self, user_id: str, result: Dict[str, Any]) -> None:
        topic = result.get("topic", "general")
        is_correct = bool(result.get("correct", False))
        self.update_subject_from_quiz(user_id, subject_id=str(topic), is_correct=is_correct)

    def update_from_coding(self, user_id: str, result: Dict[str, Any]) -> None:
        topic = result.get("topic", "coding")
        is_correct = bool(result.get("correct", False))
        self.update_subject_from_quiz(user_id, subject_id=str(topic), is_correct=is_correct)

    def update_from_exam(self, user_id: str, eval_meta: Dict[str, Any]) -> None:
        topic = eval_meta.get("topic", "general")
        is_correct = bool(eval_meta.get("correct", False))
        self.update_subject_from_quiz(user_id, subject_id=str(topic), is_correct=is_correct)

    def update_from_general(self, user_id: str, next_action: Dict[str, Any], message: str) -> None:
        msg = message.lower()
        is_correct = any(k in msg for k in ["i understand", "got it", "makes sense", "thanks", "yeah", "correct"])
        topic = (
            next_action.get("weak_topics", [next_action.get("prompt", "general")])[0]
            if next_action.get("weak_topics")
            else next_action.get("prompt", "general")
        )
        if topic not in TOPICS and topic in SUBJECTS:
            subject_id = topic
        else:
            subject_id = str(topic)
        self.update_subject_from_quiz(user_id, subject_id=subject_id, is_correct=is_correct)

    def get_weak_subjects(self, user_id: str, threshold: float = 0.55) -> List[str]:
        user = self.get_or_init_user(user_id)
        weak = []
        for sid, st in user.subjects.items():
            if st.total_attempts > 0:
                success_rate = st.correct_answers / st.total_attempts
                if success_rate < threshold:
                    weak.append(sid)
        return sorted(
            weak,
            key=lambda s: user.subjects[s].correct_answers / max(1, user.subjects[s].total_attempts),
        )

    def get_strong_subjects(self, user_id: str, threshold: float = 0.75) -> List[str]:
        user = self.get_or_init_user(user_id)
        strong = []
        for sid, st in user.subjects.items():
            if st.total_attempts > 0:
                success_rate = st.correct_answers / st.total_attempts
                if success_rate >= threshold:
                    strong.append(sid)
        return sorted(
            strong,
            key=lambda s: user.subjects[s].correct_answers / max(1, user.subjects[s].total_attempts),
            reverse=True,
        )

    def get_learning_style(self, user_id: str, subject_id: str) -> str:
        user = self.get_or_init_user(user_id)
        st = user.subjects.get(str(subject_id))
        if st is None:
            return STYLE_MIXED
        return st.learning_style

    def get_learning_speed_ema(self, user_id: str, subject_id: str) -> float:
        user = self.get_or_init_user(user_id)
        st = user.subjects.get(str(subject_id))
        if st is None:
            return 0.5
        return st.learning_speed_ema

    def get_subject_difficulty(self, user_id: str, subject_id: str) -> str:
        user = self.get_or_init_user(user_id)
        st = user.subjects.get(str(subject_id))
        if st is None:
            return DIFFICULTIES[1]
        idx = min(st.difficulty_idx, len(DIFFICULTIES) - 1)
        return DIFFICULTIES[idx]

    def get_subject_proficiency(self, user_id: str, subject_id: str) -> Dict[str, Any]:
        user = self.get_or_init_user(user_id)
        st = user.subjects.get(str(subject_id))

        if st is None:
            return {
                "success_rate": 0.0,
                "total_attempts": 0,
                "correct_answers": 0,
                "weak_score": 0,
                "strong_score": 0,
                "difficulty": "medium",
                "learning_style": "mixed",
                "learning_speed": 0.5,
                "streak": 0,
                "ready_for_challenge": False,
            }

        success_rate = st.correct_answers / max(1, st.total_attempts)
        ready_for_challenge = st.streak >= 3 and st.difficulty_idx < 2

        return {
            "success_rate": success_rate,
            "total_attempts": st.total_attempts,
            "correct_answers": st.correct_answers,
            "weak_score": st.weak_score,
            "strong_score": st.strong_score,
            "difficulty": DIFFICULTIES[min(st.difficulty_idx, len(DIFFICULTIES) - 1)],
            "learning_style": st.learning_style,
            "learning_speed": st.learning_speed_ema,
            "streak": st.streak,
            "ready_for_challenge": ready_for_challenge,
        }

    def get_learning_profile(self, user_id: str) -> Dict[str, Any]:
        user = self.get_or_init_user(user_id)

        weak = self.get_weak_subjects(user_id)
        strong = self.get_strong_subjects(user_id)

        total_attempts = sum(st.total_attempts for st in user.subjects.values())
        total_correct = sum(st.correct_answers for st in user.subjects.values())
        overall_success = (total_correct / max(1, total_attempts)) if total_attempts > 0 else 0.0

        profiles = {}
        for sid in user.subjects.keys():
            profiles[sid] = self.get_subject_proficiency(user_id, sid)

        return {
            "weak_subjects": weak,
            "strong_subjects": strong,
            "total_subjects_attempted": len(user.subjects),
            "overall_success_rate": overall_success,
            "total_attempts": total_attempts,
            "subject_profiles": profiles,
        }

    def get_teaching_recommendation(self, user_id: str, subject_id: str) -> Dict[str, Any]:
        prof = self.get_subject_proficiency(user_id, subject_id)
        success = prof["success_rate"]
        speed = prof["learning_speed"]
        style = prof["learning_style"]

        if speed < 0.4:
            pace = "slow"
        elif speed > 0.75:
            pace = "fast"
        else:
            pace = "medium"

        if success < 0.40:
            teaching_style = "gentle_scaffolding"
        elif success < 0.55:
            teaching_style = "step_by_step" if style == "steps" else "guided_probing"
        elif success < 0.75:
            teaching_style = "balanced_support"
        else:
            teaching_style = "challenge_advanced"

        if subject_id in SUBJECTS:
            subj = SUBJECTS[subject_id]
            focus_areas = list(subj.subtopics[:3]) if subj.subtopics else []
        else:
            focus_areas = []

        return {
            "teaching_style": teaching_style,
            "difficulty": prof["difficulty"],
            "pace": pace,
            "learning_style": style,
            "focus_areas": focus_areas,
        }

    def get_subjects_by_status(self, user_id: str) -> Dict[str, List[str]]:
        user = self.get_or_init_user(user_id)

        attempted = set(user.subjects.keys())
        all_subjects = set(SUBJECTS.keys())
        not_attempted = list(all_subjects - attempted)

        mastered = self.get_strong_subjects(user_id, threshold=0.75)
        struggling = self.get_weak_subjects(user_id, threshold=0.55)

        developing = []
        for sid in attempted:
            if sid not in mastered and sid not in struggling:
                developing.append(sid)

        return {
            "mastered": sorted(mastered),
            "developing": sorted(developing),
            "struggling": sorted(struggling),
            "not_attempted": sorted(not_attempted),
        }

    def get_focus_recommendation(self, user_id: str, limit: int = 3) -> List[str]:
        weak = self.get_weak_subjects(user_id)
        strong = self.get_strong_subjects(user_id)

        status = self.get_subjects_by_status(user_id)
        not_attempted = status["not_attempted"]

        recommendations = []
        recommendations.extend(weak[:limit])
        if len(recommendations) < limit:
            recommendations.extend(not_attempted[: limit - len(recommendations)])
        if len(recommendations) < limit:
            ready = [
                s
                for s in strong
                if self.get_subject_proficiency(user_id, s).get("ready_for_challenge", False)
            ]
            recommendations.extend(ready[: limit - len(recommendations)])

        return recommendations[:limit]
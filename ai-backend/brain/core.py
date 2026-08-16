from __future__ import annotations

import base64
import hashlib
import hmac
import json
import logging
import os
import re
import statistics
import threading
import time
import urllib.request
import uuid
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple, Union
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

# ============================================================================
# INTRA-PACKAGE & SIBLING RESOLVERS
# ============================================================================

from .coding_engine import CodingEngine
from .context_engine import ContextEngine
from .creative_engine import CreativeEngine
from .education_subjects_engine import EducationSubjectsEngine
from .emotion import EmotionEngine, UserEmotionState
from .exam import ExamEngine, ExamQuestion
from .learning import (
    DIFFICULTIES,
    LearningEngine,
    SubjectLearningState,
    UserLearningState,
)
from .math_engine import MathEngine
from .memory import ChatMemoryEvent, MemoryEngine
from .profession_engine import (
    CATEGORY_HINTS,
    LEVEL_TEMPLATES,
    PROFESSION_CATEGORY_KEYWORDS,
    PROFESSION_MAP,
    PROFESSION_NAMES,
    ProfessionEngine,
)
from .response_composer import ResponseComposer
from .risk_analyzer import RiskAnalyzer
from .topic_detector import TopicDetector

# Education taxonomy subject detection resolver
try:
    from legacy.education.subjects import LEVELS, SUBJECTS, Subject, detect_subject_id
except (ImportError, ValueError):
    try:
        from education.subjects import LEVELS, SUBJECTS, Subject, detect_subject_id
    except (ImportError, ValueError):
        LEVELS = {}
        SUBJECTS = {}

        def detect_subject_id(message: str, fallback: str = "mathematics") -> str:
            return fallback


# Multilingual helpers resolver
try:
    from legacy.multilingual import (
        detect_language_from_text,
        get_default_language,
        get_lang_display_name,
        get_lang_speech_locale,
        normalize_lang_code,
        supported_language_codes,
    )
except (ImportError, ValueError):
    try:
        from multilingual import (
            detect_language_from_text,
            get_default_language,
            get_lang_display_name,
            get_lang_speech_locale,
            normalize_lang_code,
            supported_language_codes,
        )
    except (ImportError, ValueError):

        def detect_language_from_text(text: str) -> str:
            return "en"

        def get_default_language() -> str:
            return "en"

        def get_lang_display_name(lang_code: str) -> str:
            return "English"

        def get_lang_speech_locale(lang_code: str) -> str:
            return "en-US"

        def normalize_lang_code(code: str) -> str:
            if not code:
                return "en"
            return code.strip().lower().split("-")[0] or "en"

        def supported_language_codes() -> List[str]:
            return [
                "en",
                "hi",
                "ja",
                "ar",
                "es",
                "fr",
                "zh",
                "ru",
                "bn",
                "ta",
                "ur",
                "de",
                "pt",
                "ko",
                "vi",
                "th",
                "id",
                "tr",
                "it",
                "te",
                "mr",
                "ms",
                "fa",
            ]


try:
    from legacy.multilingual_system import (
        BotLanguagePolicy,
        enabled_supported_languages,
        format_reply_language_marker,
        get_effective_supported_languages,
        normalize_language_list,
        pick_reply_language,
    )
except (ImportError, ValueError):
    try:
        from multilingual_system import (
            BotLanguagePolicy,
            enabled_supported_languages,
            format_reply_language_marker,
            get_effective_supported_languages,
            normalize_language_list,
            pick_reply_language,
        )
    except (ImportError, ValueError):

        @dataclass
        class BotLanguagePolicy:
            use_global_language_system: bool = True
            selected_languages: Optional[List[str]] = None

            @staticmethod
            def from_state(state: Dict[str, Any] | None) -> BotLanguagePolicy:
                s = state or {}
                use_global = bool(s.get("useGlobalLanguageSystem", True))
                langs = s.get("selectedLanguages") or s.get("selected_languages") or None
                if isinstance(langs, str):
                    langs = [langs]
                if isinstance(langs, list):
                    langs = [normalize_lang_code(x) for x in langs if x]
                else:
                    langs = None
                return BotLanguagePolicy(use_global_language_system=use_global, selected_languages=langs)

        def normalize_language_list(langs: Optional[List[str]]) -> List[str]:
            if not langs:
                return []
            out: List[str] = []
            for x in langs:
                if x:
                    out.append(normalize_lang_code(str(x)))
            seen = set()
            deduped: List[str] = []
            for x in out:
                if x not in seen:
                    seen.add(x)
                    deduped.append(x)
            return deduped

        def enabled_supported_languages() -> List[str]:
            return supported_language_codes()

        def get_effective_supported_languages(policy: BotLanguagePolicy) -> List[str]:
            if policy.use_global_language_system:
                return enabled_supported_languages()
            return normalize_language_list(policy.selected_languages)

        def pick_reply_language(
            *,
            policy: BotLanguagePolicy,
            detected_lang: str,
            preferred_lang: Optional[str] = None,
        ) -> str:
            detected_lang = normalize_lang_code(detected_lang)
            if policy.use_global_language_system:
                return detected_lang
            preferred = normalize_lang_code(preferred_lang) if preferred_lang else None
            supported = get_effective_supported_languages(policy)
            if preferred and (not supported or preferred in supported):
                return preferred
            if supported and detected_lang in supported:
                return detected_lang
            if supported:
                return supported[0]
            return get_default_language()

        def format_reply_language_marker(lang_code: str) -> str:
            code = normalize_lang_code(lang_code)
            return f"[{code.upper()}]"


# Image system resolver
try:
    from legacy.image.image_system import (
        ImageIntent,
        ImageStylePlan,
        analyze_image_fake,
        detect_image_intent,
        generate_image_fake,
        plan_style_and_quality,
        safety_block,
    )
except (ImportError, ValueError):
    try:
        from image.image_system import (
            ImageIntent,
            ImageStylePlan,
            analyze_image_fake,
            detect_image_intent,
            generate_image_fake,
            plan_style_and_quality,
            safety_block,
        )
    except (ImportError, ValueError):

        def detect_image_intent(message: str):
            return None

        def plan_style_and_quality(prompt: str):
            return None

        def generate_image_fake(
            prompt: str,
            plan: Any,
            seed: Optional[int] = None,
            feedback_stats: Optional[Dict[str, int]] = None,
        ):
            return {}

        def analyze_image_fake(image_b64_or_url: str, prompt: str = ""):
            return {}

        def safety_block(prompt: str):
            return None


def _resolve_puzzle_engine(storage_path: str):
    try:
        from legacy.puzzle.puzzle_engine import PuzzleEngine

        return PuzzleEngine(storage_path=storage_path)
    except (ImportError, ValueError):
        try:
            from puzzle.puzzle_engine import PuzzleEngine

            return PuzzleEngine(storage_path=storage_path)
        except (ImportError, ValueError):
            return None


# ============================================================================
# ROUTING INFRASTRUCTURE
# ============================================================================


@dataclass
class ChatPipelineResult:
    reply: str
    emotion: str
    topic: str


class AIRouter:
    """Central AI router."""

    def __init__(self, brain: Any) -> None:
        self.brain = brain
        self.priority = {
            "image": 10,
            "math": 15,
            "coding": 20,
            "creative": 35,
            "education": 40,
            "exam": 45,
            "puzzle": 50,
            "web": 60,
            "voice": 70,
            "memory": 80,
            "emotion": 90,
        }

    def _detect_candidates(self, message: str) -> List[str]:
        cand: List[str] = []

        # Image generation / analysis check
        img_intent = detect_image_intent(message)
        if img_intent:
            cand.append("image")

        math_engine: MathEngine = self.brain.get_engine("math")
        if math_engine and math_engine.is_math_expression(message):
            cand.append("math")

        m = (message or "").lower()
        if any(
            k in m
            for k in [
                "joke",
                "riddle",
                "poem",
                "story",
                "limerick",
                "sonnet",
                "write me",
                "tell me a",
                "make me a",
            ]
        ):
            cand.append("creative")
        if m.startswith("#code") or any(
            k in m
            for k in [
                "function ",
                "def ",
                "class ",
                "react",
                "javascript",
                "python",
                "typescript",
                "fastapi",
            ]
        ):
            cand.append("coding")
        if m.startswith("#question") or any(k in m for k in ["practice", "explain", "lesson", "topic:"]):
            cand.append("education")
        if any(k in m for k in ["puzzle", "riddle", "sudoku", "crossword", "anagram", "kakuro"]):
            cand.append("puzzle")
        if any(q in m for q in ["who is", "when is", "where is", "search:", "news", "stock", "latest", "find:"]):
            cand.append("web")
        if any(k in m for k in ["remember", "remind me", "save this", "note:"]):
            cand.append("memory")
        if any(k in m for k in ["how do i say", "pronounce", "translate"]):
            cand.append("voice")

        cand.append("emotion")

        seen = set()
        out: List[str] = []
        for c in cand:
            if c not in seen:
                seen.add(c)
                out.append(c)
        return out

    def _rank(self, candidates: List[str]) -> List[str]:
        return sorted(candidates, key=lambda x: self.priority.get(x, 999))

    def route(self, user_id: str, message: str, bot_id: str | None = None) -> Dict[str, Any] | None:
        try:
            if not message or not message.strip():
                return None

            candidates = self._detect_candidates(message)
            if not candidates or candidates == ["emotion"]:
                return None

            ranked = self._rank(candidates)

            emotion_engine = self.brain.get_engine("emotion")
            try:
                emotion = emotion_engine.detect_and_update(user_id=user_id, message=message)
            except Exception:
                emotion = "neutral"

            primary = ranked[0]

            if primary == "image":
                intent = detect_image_intent(message)
                if intent and intent.action == "generate":
                    block_reason = safety_block(intent.prompt)
                    if block_reason:
                        return {
                            "reply": f"[Safety] Image request blocked: {block_reason}.",
                            "emotion": "neutral",
                            "topic": "image",
                        }

                    plan = plan_style_and_quality(intent.prompt)
                    feedback = self.brain.memory.get_image_feedback(f"{plan.style}_{plan.quality}".replace(" ", "_"))
                    gen = generate_image_fake(prompt=intent.prompt, plan=plan, feedback_stats=feedback)
                    img_data = gen.get("image", {})
                    data_url = img_data.get("data_url", "")

                    action = {
                        "type": "generate",
                        "status": "done",
                        "prompt": intent.prompt,
                        "style": plan.style,
                        "quality": plan.quality,
                        "aspect": plan.aspect,
                        "image": img_data,
                    }
                    self.brain.memory.append_image_history(user_id=user_id, image_action=action)

                    reply_text = (
                        f"Generated image ({plan.style} • {plan.quality})\n\n"
                        f"![{intent.prompt}]({data_url})\n\n"
                        f"*Prompt:* {intent.prompt}"
                    )
                    return {
                        "reply": reply_text,
                        "emotion": "happy",
                        "topic": "image",
                        "imageAction": action,
                        "image": img_data,
                    }

            replies: List[str] = []
            topic = primary

            if primary == "math":
                res = self.brain.invoke_engine("math", "solve", message, user_id=user_id, as_teaching=True)
                reply = res.get("reply") if isinstance(res, dict) else (str(res) if res is not None else "")
                replies.append(reply)
                topic = res.get("topic", "math") if isinstance(res, dict) else "math"

            elif primary == "coding":
                res = self.brain.invoke_engine("coding", "generate_code", message, user_id=user_id)
                reply = res.get("reply") if isinstance(res, dict) else (str(res) if res is not None else "")
                if isinstance(res, dict):
                    reply = res.get("reply") or res.get("fixed_code") or (res.get("reply_text") if "reply_text" in res else reply)
                replies.append(reply)
                topic = "coding"

            elif primary == "creative":
                res = self.brain.invoke_engine("creative", "generate", user_id=user_id, message=message)
                reply = res.get("reply") if isinstance(res, dict) else (str(res) if res is not None else "")
                replies.append(reply)
                topic = "creative"

            elif primary == "education":
                try:
                    prof = self.brain.invoke_engine("learning", "decide_next_action", user_id, message or "general")
                    reply = f"Study plan: {prof.get('prompt', 'practice')}." if isinstance(prof, dict) else str(prof or "I can help with learning.")
                except Exception:
                    reply = "I can help with learning. Tell me a topic to focus on."
                replies.append(reply)
                topic = "education"

            elif primary == "web":
                try:
                    search_result = self.brain._handle_live_web_search(
                        user_id=user_id,
                        query=message,
                        language=None,
                        trusted_sources=[],
                        allowed_categories=[],
                    )
                    if search_result:
                        replies.append(search_result.get("reply", ""))
                        topic = "web_search"
                except Exception:
                    pass

            elif primary == "puzzle":
                try:
                    res_pair = self.brain.invoke_engine("exam", "handle_question", message)
                    if isinstance(res_pair, tuple) and len(res_pair) >= 1:
                        res = res_pair[0]
                    else:
                        res = res_pair
                    replies.append(res if res is not None else "")
                    topic = "puzzle"
                except Exception:
                    replies.append("I can help with puzzles — tell me the puzzle details.")
                    topic = "puzzle"

            elif primary == "memory":
                replies.append("Memory operation queued. Use Tasks to inspect progress.")
                topic = "memory"

            else:
                return None

            prefix = f"(Feeling: {emotion}) " if (emotion and emotion != "neutral") else ""
            final_reply = prefix + "\n\n".join([r for r in replies if r])
            return {"reply": final_reply.strip(), "emotion": emotion or "neutral", "topic": topic}

        except Exception:
            return None


class TaskAgent:
    """High-level background task agent for asynchronous pipelines."""

    def __init__(self, brain: Any) -> None:
        self.brain = brain

    def submit_task(self, task_type: str, user_id: str, payload: Dict[str, Any] | None = None) -> str:
        payload = payload or {}

        def generate_study_sheet(uid: str, p: Dict[str, Any], progress_callback=None):
            learning = self.brain.get_engine("learning")
            try:
                profile = learning.get_learning_profile(uid)
            except Exception:
                profile = {}
            topic = p.get("topic") or "general"
            sheet = (
                f"Study Sheet for {topic}\n\n"
                "Key points:\n"
                "- Review fundamentals\n"
                "- Work on practice problems\n"
                "- Check solutions and hints\n"
                "- Validate with step-by-step checklists\n"
            )
            return {"type": "study_sheet", "topic": topic, "sheet": sheet, "profile": profile}

        def create_file(uid: str, p: Dict[str, Any], progress_callback=None):
            path = p.get("path") or "notes.txt"
            content = p.get("content") or ""
            data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
            os.makedirs(data_dir, exist_ok=True)
            full = os.path.abspath(os.path.join(data_dir, path))
            with open(full, "w", encoding="utf-8") as f:
                f.write(content)
            return {"ok": True, "path": full}

        def web_search_task(uid: str, p: Dict[str, Any], progress_callback=None):
            query = str(p.get("query") or "")
            lang = str(p.get("language") or "en")
            return self.brain._handle_live_web_search(user_id=uid, query=query, language=lang, progress_callback=progress_callback)

        def math_solve_task(uid: str, p: Dict[str, Any], progress_callback=None):
            expr = str(p.get("expression") or "")
            math_eng = self.brain.get_engine("math")
            return math_eng.solve(expr, user_id=uid, as_teaching=True, progress_callback=progress_callback)

        def coding_gen_task(uid: str, p: Dict[str, Any], progress_callback=None):
            req = str(p.get("prompt") or "")
            code_eng = self.brain.get_engine("coding")
            return code_eng.generate_code(req, user_id=uid, progress_callback=progress_callback)

        handlers = {
            "generate_study_sheet": generate_study_sheet,
            "create_file": create_file,
            "web_search": web_search_task,
            "math_solve": math_solve_task,
            "coding_gen": coding_gen_task,
        }

        handler = handlers.get(task_type)
        if not handler:

            def _unknown(uid, p, progress_callback=None):
                return {"ok": False, "error": f"Unknown task type: {task_type}"}

            handler = _unknown

        return self.brain.submit_background_task(handler, user_id, payload)


# ============================================================================
# CORE BRAIN MAIN ENGINE
# ============================================================================


class CoreBrain:
    """Core intelligence engine coordinating all specialized AI capabilities."""

    def __init__(self, storage_path: str, bot_market: object | None = None) -> None:
        self._engine_factories: Dict[str, Any] = {
            "emotion": lambda: EmotionEngine(storage_path=storage_path),
            "topic_detector": lambda: TopicDetector(),
            "risk": lambda: RiskAnalyzer(),
            "memory": lambda: MemoryEngine(storage_path=storage_path),
            "learning": lambda: LearningEngine(storage_path=storage_path),
            "exam": lambda: ExamEngine(),
            "math": lambda: MathEngine(),
            "creative": lambda: CreativeEngine(storage_path=storage_path),
            "coding": lambda: CodingEngine(),
            "profession": lambda: ProfessionEngine(),
            "composer": lambda: ResponseComposer(),
            "context": lambda: ContextEngine(storage_path=storage_path),
        }
        self._engines: Dict[str, Any] = {}
        self._engines_lock = threading.RLock()

        for name, factory in list(self._engine_factories.items()):
            try:
                inst = factory()
                self._engines[name] = inst
                setattr(self, name, inst)
            except Exception:
                pass

        self._bots_storage_path = storage_path
        self.bot_market = bot_market
        self._executor = ThreadPoolExecutor(max_workers=4)

        self._response_cache: OrderedDict[str, Dict[str, Any]] = OrderedDict()
        self._response_cache_lock = threading.RLock()
        self._response_cache_max = 200
        self._response_cache_ttl = 3600

        self._metrics_lock = threading.RLock()
        self._metrics: Dict[str, Any] = {
            "cache_hits": 0,
            "cache_misses": 0,
            "cache_sets": 0,
            "engine_calls": {},
            "engine_latency_ms": {},
        }
        self._logger = logging.getLogger(__name__)

        self._bg_tasks: Dict[str, Dict[str, Any]] = {}
        self._bg_tasks_lock = threading.RLock()

        self.router = AIRouter(self)
        self.task_agent = TaskAgent(self)

    def get_engine(self, name: str) -> Any | None:
        name = (name or "").strip()
        if not name:
            return None
        with self._engines_lock:
            if name in self._engines:
                return self._engines[name]
            factory = self._engine_factories.get(name)
            if not factory:
                return None
            try:
                inst = factory()
                self._engines[name] = inst
                setattr(self, name, inst)
                return inst
            except Exception:
                return None

    def invoke_engine(self, engine_name: str, method_name: str | None = None, *args, timeout: int = 8, **kwargs) -> Any:
        engine = self.get_engine(engine_name)
        if engine is None:
            return None

        if method_name:
            if not hasattr(engine, method_name):
                return None
            func = lambda: getattr(engine, method_name)(*args, **kwargs)
        else:
            if callable(engine):
                func = lambda: engine(*args, **kwargs)
            else:
                return None

        start = time.time()
        with self._metrics_lock:
            try:
                ec = self._metrics.setdefault("engine_calls", {})
                ec[engine_name] = ec.get(engine_name, 0) + 1
            except Exception:
                pass

        future = self._executor.submit(func)
        try:
            res = future.result(timeout=timeout)
            elapsed_ms = int((time.time() - start) * 1000)
            with self._metrics_lock:
                try:
                    lat = self._metrics.setdefault("engine_latency_ms", {}).setdefault(engine_name, [])
                    lat.append(elapsed_ms)
                    if len(lat) > 200:
                        del lat[:-200]
                except Exception:
                    pass
            return res
        except Exception:
            try:
                future.cancel()
            except Exception:
                pass
            return None

    def get_metrics(self) -> Dict[str, Any]:
        with self._metrics_lock:
            snapshot = {k: v for k, v in self._metrics.items() if k != "engine_latency_ms"}
            lat_snapshot: Dict[str, Dict[str, Any]] = {}
            for name, samples in self._metrics.get("engine_latency_ms", {}).items():
                try:
                    lat_snapshot[name] = {
                        "count": len(samples),
                        "avg_ms": int(statistics.mean(samples)) if samples else None,
                        "p95_ms": int(sorted(samples)[int(len(samples) * 0.95)]) if samples else None,
                    }
                except Exception:
                    lat_snapshot[name] = {"count": len(samples)}
            snapshot["engine_latency_summary"] = lat_snapshot
            return snapshot

    def cache_get(self, key: str) -> Any | None:
        if not key:
            return None
        with self._response_cache_lock:
            entry = self._response_cache.get(key)
            if not entry:
                with self._metrics_lock:
                    try:
                        self._metrics["cache_misses"] += 1
                    except Exception:
                        pass
                return None
            try:
                ts = entry.get("ts")
                if ts and (time.time() - ts) > entry.get("ttl", self._response_cache_ttl):
                    del self._response_cache[key]
                    with self._metrics_lock:
                        try:
                            self._metrics["cache_misses"] += 1
                        except Exception:
                            pass
                    return None
            except Exception:
                return None

            self._response_cache.move_to_end(key)
            with self._metrics_lock:
                try:
                    self._metrics["cache_hits"] += 1
                except Exception:
                    pass
            return entry.get("value")

    def cache_set(self, key: str, value: Any, ttl: int | None = None) -> None:
        if not key:
            return
        with self._response_cache_lock:
            now = time.time()
            self._response_cache[key] = {"ts": now, "ttl": ttl or self._response_cache_ttl, "value": value}
            self._response_cache.move_to_end(key)
            while len(self._response_cache) > self._response_cache_max:
                self._response_cache.popitem(last=False)
        with self._metrics_lock:
            try:
                self._metrics["cache_sets"] += 1
            except Exception:
                pass

    def submit_background_task(self, func: Callable, *args, **kwargs) -> str:
        tid = str(uuid.uuid4())
        with self._bg_tasks_lock:
            self._bg_tasks[tid] = {
                "status": "queued",
                "result": None,
                "error": None,
                "ts": time.time(),
                "progress": 0,
                "started_at": None,
                "end_at": None,
            }

        def _run():
            with self._bg_tasks_lock:
                self._bg_tasks[tid]["status"] = "running"
                self._bg_tasks[tid]["started_at"] = int(time.time() * 1000)
                self._bg_tasks[tid]["progress"] = 0
            try:
                try:
                    res = func(*args, progress_callback=lambda p: self._update_task_progress(tid, p), **kwargs)
                except TypeError:
                    res = func(*args, **kwargs)

                with self._bg_tasks_lock:
                    self._bg_tasks[tid]["status"] = "completed"
                    self._bg_tasks[tid]["result"] = res
                    self._bg_tasks[tid]["progress"] = 100
                    self._bg_tasks[tid]["end_at"] = int(time.time() * 1000)
            except Exception as e:
                with self._bg_tasks_lock:
                    self._bg_tasks[tid]["status"] = "failed"
                    self._bg_tasks[tid]["error"] = str(e)
                    self._bg_tasks[tid]["end_at"] = int(time.time() * 1000)

        self._executor.submit(_run)
        return tid

    def _update_task_progress(self, tid: str, progress: int | float) -> None:
        try:
            p = int(max(0, min(100, round(float(progress)))))
            with self._bg_tasks_lock:
                if tid in self._bg_tasks:
                    self._bg_tasks[tid]["progress"] = p
        except Exception:
            pass

    def get_background_task(self, task_id: str) -> Dict[str, Any] | None:
        with self._bg_tasks_lock:
            t = self._bg_tasks.get(task_id)
            if t is None:
                return None
            return {
                "status": t.get("status"),
                "result": t.get("result"),
                "error": t.get("error"),
                "progress": t.get("progress", 0),
                "started_at": t.get("started_at"),
                "end_at": t.get("end_at"),
                "ts": int(t.get("ts") * 1000) if t.get("ts") else None,
            }

    def _try_upstream_llm_completion(
        self,
        messages: List[Dict[str, str]],
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Optional[str]:
        """Attempt upstream LLM completions if API key / endpoint is configured."""
        resolved_key = api_key or os.environ.get("NITRO_SYSTEM_API_KEY") or os.environ.get("OPENROUTER_API_KEY")
        if not resolved_key:
            return None

        base_url = os.environ.get("NITRO_API_BASE", "https://openrouter.ai").rstrip("/")
        url = f"{base_url}/api/v1/chat/completions"

        chosen_model = model or os.environ.get("NITRO_DEFAULT_MODEL", "meta-llama/llama-3-8b-instruct:free")
        payload = {
            "model": chosen_model,
            "messages": messages,
            "stream": False,
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {resolved_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://nitro-ai.local",
                    "X-Title": "Nitro Infinity AI",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                choice = data.get("choices", [{}])[0]
                content = choice.get("message", {}).get("content")
                return str(content).strip() if content else None
        except Exception:
            return None

    def handle_message(
        self,
        user_id: str,
        message: str,
        persist_chat: bool = True,
        bot_id: str | None = None,
        incoming_language: str | None = None,
        conversation_context: Optional[List[Dict[str, str]]] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ) -> Dict[str, Any]:
        chat_mode = self._parse_chat_mode(message)
        clean_message = self._strip_chat_commands(message)
        save_chat = persist_chat and not str(user_id).startswith("guest_")

        # 1. Multimodal Image Intent Detection & Routing
        img_intent = detect_image_intent(clean_message)
        if img_intent and img_intent.action == "generate":
            block_reason = safety_block(img_intent.prompt)
            if block_reason:
                gated_reply = f"[Safety] Image request blocked: {block_reason}."
                if save_chat:
                    self.memory.append_message(user_id, clean_message, gated_reply, emotion="neutral", topic="image")
                return {"reply": gated_reply, "emotion": "neutral", "topic": "image"}

            # Bot image generation policy check
            bot_meta = self.bot_market.get_bot(bot_id) if (bot_id and getattr(self, "bot_market", None)) else {}
            bot_img_state = self.memory.load_bot_image_policy(user_id=user_id, bot_id=bot_id) if bot_id else {}
            img_gen_enabled = bool(bot_meta.get("imageGenerationEnabled", True) if bot_id else True)
            if bot_id and not img_gen_enabled:
                gated_reply = "Image generation is disabled in this bot's configuration."
                if save_chat:
                    self.memory.append_message(user_id, clean_message, gated_reply, emotion="neutral", topic="image")
                return {"reply": gated_reply, "emotion": "neutral", "topic": "image"}

            plan = plan_style_and_quality(img_intent.prompt)
            feedback = self.memory.get_image_feedback(f"{plan.style}_{plan.quality}".replace(" ", "_"))
            gen = generate_image_fake(prompt=img_intent.prompt, plan=plan, feedback_stats=feedback)
            img_data = gen.get("image", {})
            data_url = img_data.get("data_url", "")

            action = {
                "type": "generate",
                "status": "done",
                "prompt": img_intent.prompt,
                "style": plan.style,
                "quality": plan.quality,
                "aspect": plan.aspect,
                "image": img_data,
            }
            self.memory.append_image_history(user_id=user_id, image_action=action)

            reply_text = (
                f"Generated image ({plan.style} • {plan.quality})\n\n"
                f"![{img_intent.prompt}]({data_url})\n\n"
                f"*Prompt:* {img_intent.prompt}"
            )
            if save_chat:
                self.memory.append_message(user_id, clean_message, reply_text, emotion="happy", topic="image")
            return {
                "reply": reply_text,
                "emotion": "happy",
                "topic": "image",
                "imageAction": action,
                "image": img_data,
            }

        # 2. Context and Pronoun Resolution
        try:
            is_guest = isinstance(user_id, str) and user_id.startswith("guest_")
            if bot_id:
                bot_ctx_state = self.memory.load_bot_context_policy(user_id=user_id, bot_id=bot_id)
                context_enabled = bool(bot_ctx_state.get("contextUnderstandingEnabled", False))
                history_allowed = bool(bot_ctx_state.get("useUserHistoryUnderstanding", False)) and not is_guest
            else:
                context_enabled = True
                history_allowed = not is_guest

            if context_enabled:
                ctx_engine = self.get_engine("context")
                try:
                    analysis = ctx_engine.analyze_message(
                        user_id=user_id,
                        message=clean_message,
                        bot_id=bot_id,
                        use_saved_history=history_allowed,
                    )
                    conf = float(analysis.get("confidence", 1.0) or 0.0)
                    if conf < 0.35 and analysis.get("clarification"):
                        clar = analysis.get("clarification")
                        if save_chat:
                            self.memory.append_message(
                                user_id,
                                clean_message,
                                clar,
                                emotion="neutral",
                                topic="clarification",
                            )
                        return {"reply": clar, "emotion": "neutral", "topic": "clarification"}
                    resolved = analysis.get("resolved_message")
                    if resolved and resolved != clean_message:
                        clean_message = resolved
                except Exception:
                    pass

            routed = self.router.route(user_id=user_id, message=clean_message, bot_id=bot_id)
            if routed:
                if save_chat:
                    self.memory.append_message(
                        user_id,
                        clean_message,
                        routed.get("reply", ""),
                        emotion=routed.get("emotion", "neutral"),
                        topic=routed.get("topic", "general"),
                    )
                return routed
        except Exception:
            pass

        # 3. Multilingual policy resolution
        detected_lang = normalize_lang_code(incoming_language or detect_language_from_text(clean_message))
        user_state = self.memory.load_user_state(user_id)

        policy = BotLanguagePolicy(use_global_language_system=True)
        preferred_lang = user_state.get("preferred_language")

        bot_meta = {}
        if bot_id:
            bot_policy_state = self.memory.load_bot_language_policy(user_id=user_id, bot_id=bot_id)
            policy = BotLanguagePolicy.from_state(bot_policy_state)
            preferred_lang = self.memory.load_bot_preferred_language(user_id=user_id, bot_id=bot_id) or preferred_lang

            bot_meta = self.bot_market.get_bot(bot_id) if getattr(self, "bot_market", None) else {}
            bot_edu_state = self.memory.load_bot_education_policy(user_id=user_id, bot_id=bot_id)
            education_enabled = bool(bot_meta.get("educationEnabled", False) or bot_edu_state.get("educationEnabled", False))
            bot_prof_state = self.memory.load_bot_profession_policy(user_id=user_id, bot_id=bot_id)
            profession_enabled = bool(bot_meta.get("professionEnabled", False) or bot_prof_state.get("professionEnabled", False))
        else:
            education_enabled = True
            profession_enabled = True

        reply_lang = pick_reply_language(
            policy=policy,
            detected_lang=detected_lang,
            preferred_lang=preferred_lang,
        )

        language_marker = format_reply_language_marker(reply_lang)
        reply_lang = normalize_lang_code(reply_lang)

        user_state.setdefault("language_history", [])
        user_state.setdefault("preferred_language", "en")
        self.memory.append_language_history(user_id, detected_lang)

        def _mark(s: str) -> str:
            if reply_lang == "en" or not s:
                return s
            return f"{language_marker} {s}".strip()

        emotion = self.get_engine("emotion").detect_and_update(user_id=user_id, message=clean_message)
        topic = "general"

        # 4. Math & Calculation Pipeline
        math_engine: MathEngine = self.get_engine("math")
        if math_engine and (math_engine.is_math_expression(clean_message) or clean_message.strip().startswith("#solve")):
            math_res = math_engine.solve(clean_message, user_id=user_id, as_teaching=True)
            self.learning.update_from_math(user_id, math_res)
            if math_res.get("mistake"):
                self.memory.record_mistake(user_id, math_res)

            risk_result = self.risk.analyze(clean_message, user_id=user_id)
            final = (
                self.invoke_engine(
                    "composer",
                    "compose",
                    user_id=user_id,
                    emotion=emotion,
                    topic="algebra",
                    risk_result=risk_result,
                    base_reply=math_res.get("reply", ""),
                    learning_update=math_res,
                    chat_mode=chat_mode,
                )
                or ""
            )
            if save_chat:
                self.memory.append_message(user_id, clean_message, final, emotion=emotion, topic="algebra")
            return {"reply": _mark(final), "emotion": emotion, "topic": "algebra"}

        # 5. Search & Web Intelligence
        bot_web_state = {}
        web_enabled = True
        allowed_web_categories = []
        trusted_web_sources = []

        if bot_id:
            bot_web_state = self.memory.load_bot_web_policy(user_id=user_id, bot_id=bot_id)
            web_enabled = bool(bot_meta.get("webSearchEnabled", False) or bot_web_state.get("webSearchEnabled", False))
            allowed_web_categories = list(bot_meta.get("allowedWebCategories") or bot_web_state.get("allowedWebCategories") or [])
            trusted_web_sources = list(bot_meta.get("trustedSources") or bot_web_state.get("trustedSources") or [])

        search_query = self._is_live_search_query(clean_message)
        if search_query:
            if bot_id and not web_enabled:
                gated = f"{language_marker} This bot has web intelligence disabled. Please enable webSearchEnabled in bot settings."
                if save_chat:
                    self.memory.append_message(user_id, clean_message, gated, emotion=emotion, topic="web_search")
                return {"reply": _mark(gated), "emotion": emotion, "topic": "web_search"}

            query_category = self._detect_web_category(clean_message)
            if bot_id and allowed_web_categories and query_category not in [c.lower() for c in allowed_web_categories]:
                gated = f"{language_marker} This bot is configured to search only: {', '.join(allowed_web_categories)}."
                if save_chat:
                    self.memory.append_message(user_id, clean_message, gated, emotion=emotion, topic="web_search")
                return {"reply": _mark(gated), "emotion": emotion, "topic": "web_search"}

            search_result = self._handle_live_web_search(
                user_id=user_id,
                query=clean_message,
                language=reply_lang,
                trusted_sources=trusted_web_sources,
                allowed_categories=[c.lower() for c in allowed_web_categories],
            )
            if search_result:
                reply = search_result["reply"]
                if save_chat:
                    self.memory.append_message(user_id, clean_message, reply, emotion=emotion, topic="web_search")
                return {
                    "reply": _mark(reply),
                    "emotion": emotion,
                    "topic": "web_search",
                    "sources": search_result.get("sources", []),
                }

        # 6. Upstream Context Completion or Dynamic Evaluation
        msg_payload = conversation_context or [{"role": "user", "content": clean_message}]
        upstream_reply = self._try_upstream_llm_completion(messages=msg_payload, api_key=api_key, model=model)
        if upstream_reply:
            risk_result = self.risk.analyze(clean_message, user_id=user_id)
            final = (
                self.invoke_engine(
                    "composer",
                    "compose",
                    user_id=user_id,
                    emotion=emotion,
                    topic="general",
                    risk_result=risk_result,
                    base_reply=upstream_reply,
                    learning_update=None,
                    chat_mode=chat_mode,
                )
                or upstream_reply
            )
            if save_chat:
                self.memory.append_message(user_id, clean_message, final, emotion=emotion, topic="general")
            return {"reply": _mark(final), "emotion": emotion, "topic": "general"}

        # 7. Context-Aware Dynamic Fallback Generator
        topic = self.topic_detector.detect_topic(clean_message)
        reply = self._get_general_reply(user_id=user_id, message=clean_message, emotion=emotion, topic=topic)
        risk_result = self.risk.analyze(clean_message, user_id=user_id)
        final = (
            self.invoke_engine(
                "composer",
                "compose",
                user_id=user_id,
                emotion=emotion,
                topic=topic,
                risk_result=risk_result,
                base_reply=reply,
                learning_update=None,
                chat_mode=chat_mode,
            )
            or reply
        )
        if save_chat:
            self.memory.append_message(user_id, clean_message, final, emotion=emotion, topic=topic)
        return {"reply": _mark(final), "emotion": emotion, "topic": topic}

    def _is_live_search_query(self, message: str) -> bool:
        if not message:
            return False

        math_eng: MathEngine = self.get_engine("math")
        if math_eng and math_eng.is_math_expression(message):
            return False

        lower = message.strip().lower()
        triggers = [
            "search:",
            "find:",
            "look up",
            "web search",
            "browser",
            "who is",
            "who was",
            "when is",
            "where is",
            "stock price",
            "weather in",
            "latest news",
            "breaking news",
        ]
        return any(lower.startswith(t) for t in triggers)

    def _detect_web_category(self, message: str) -> str:
        lower = message.lower()
        categories = {
            "technology": ["technology", "tech", "software", "ai", "computer", "internet", "coding"],
            "science": ["science", "research", "physics", "chemistry", "biology", "space"],
            "health": ["health", "medicine", "medical", "doctor", "wellness", "fitness", "nutrition"],
            "finance": ["finance", "stock", "stocks", "market", "economy", "investment", "crypto"],
            "sports": ["sports", "score", "game", "team", "match", "league", "tournament"],
            "news": ["news", "breaking", "headline", "today"],
        }
        for category, keywords in categories.items():
            if any(keyword in lower for keyword in keywords):
                return category
        return "news"

    def _handle_live_web_search(
        self,
        user_id: str,
        query: str,
        language: str | None,
        trusted_sources: list[str] | None = None,
        allowed_categories: list[str] | None = None,
        progress_callback: Callable[[int], None] | None = None,
    ) -> Dict[str, Any]:
        def _progress(value: int) -> None:
            if progress_callback is None:
                return
            try:
                progress_callback(max(0, min(100, int(value))))
            except Exception:
                pass

        _progress(10)
        lang_code = language or "en"

        search_data = self._query_web_search(query, language=lang_code)
        sources = search_data.get("sources", [])
        if not sources:
            _progress(100)
            return {
                "reply": f"Unable to fetch live web search results for '{query}' at the moment.",
                "sources": [],
            }

        _progress(80)
        reply = self._format_web_search_reply(
            query=query,
            results=sources,
            language=lang_code,
            trusted_sources=trusted_sources,
        )
        _progress(100)
        return {"reply": reply, "sources": sources[:4], "cached": False}

    def _query_web_search(self, query: str, language: str = "en") -> Dict[str, Any]:
        query_text = query.strip()
        if not query_text:
            return {"sources": []}

        search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(query_text)}"
        accept_lang = (language or "en").replace("_", "-")
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": f"{accept_lang},en;q=0.8",
        }

        try:
            request = urllib.request.Request(search_url, headers=headers)
            with urllib.request.urlopen(request, timeout=12) as response:
                html_body = response.read().decode("utf-8", errors="ignore")
        except (HTTPError, URLError, ValueError):
            return {"sources": []}

        results = []
        entries = re.findall(r'<a[^>]+class="result__a"[^>]+href="([^"]+)"[^>]*>(.*?)</a>', html_body, flags=re.S)
        snippets = re.findall(r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>', html_body, flags=re.S)
        for idx, (href, title_html) in enumerate(entries[:6]):
            title = re.sub(r"<.*?>", "", title_html).strip()
            url = href.strip()
            if "/l/?kh=" in url and "uddg=" in url:
                parsed = urlparse(url)
                decoded = parse_qs(parsed.query).get("uddg")
                if decoded:
                    url = unquote(decoded[0])
            snippet = re.sub(r"<.*?>", "", snippets[idx].strip()) if idx < len(snippets) else ""
            domain = urlparse(url).netloc.lower()
            if not url or not domain:
                continue
            results.append({
                "title": title or url,
                "url": url,
                "snippet": snippet,
                "domain": domain,
                "trusted": any(t in domain for t in ["wikipedia.org", "bbc.co.uk", "nytimes.com", "cnn.com", "reuters.com", "nature.com"]),
            })
        return {"sources": results}

    def _format_web_search_reply(
        self,
        query: str,
        results: list[Dict[str, str]],
        language: str,
        trusted_sources: list[str] | None = None,
    ) -> str:
        reply_parts = [f"Search results for **{query}**:"]
        for idx, result in enumerate(results[:3], start=1):
            reply_parts.append(f"{idx}. **{result['title']}** ({result['domain']})")
            if result.get("snippet"):
                reply_parts.append(f"   {result['snippet']}")
            reply_parts.append(f"   {result['url']}")
        return "\n\n".join(reply_parts)

    def _parse_chat_mode(self, message: str) -> Dict[str, bool]:
        return {
            "strict": message.strip().startswith("#strict"),
            "friendly": True,
            "best": True,
            "fast": False,
        }

    def _strip_chat_commands(self, message: str) -> str:
        commands = [
            "#strict",
            "#explain",
            "#summary",
            "#learn",
            "#quiz",
            "#worksheet",
            "#studyplan",
            "#question",
            "#answer",
            "#solve",
            "#code",
            "#debug",
            "#puzzle",
        ]
        clean = message.strip()
        for cmd in commands:
            if clean.lower().startswith(cmd):
                clean = clean[len(cmd) :].strip()
                break
        return clean

    def _get_general_reply(
        self,
        user_id: str,
        message: str,
        emotion: str,
        topic: str,
    ) -> str:
        low = (message or "").strip().lower()

        if any(w in low for w in ["hello", "hi", "hey", "greetings", "good morning", "good evening", "namaste"]):
            return (
                "Hello! I am Nitro Infinity AI. I'm ready to assist you with reasoning, coding, math problems, "
                "concept explanations, image generation, or general workflows. What would you like to work on today?"
            )

        if any(w in low for w in ["who are you", "what can you do", "help me", "capabilities"]):
            return (
                "Here is what I can help you with:\n\n"
                "• **Image Studio:** Generate digital art, wallpapers, sketches, or 3D renders (`make an image of...`).\n"
                "• **Mathematics & Calculus:** Step-by-step problem solving, algebra, roots, and derivatives.\n"
                "• **Programming & Coding:** Python, JavaScript/React, debugging, and API design.\n"
                "• **Learning & Education:** Adaptive lesson plans, practice questions, and concept reviews.\n"
                "• **Workflow & Career:** Professional task breakdown and domain guidance.\n\n"
                "Feel free to ask a specific question or give me a task!"
            )

        if any(w in low for w in ["thank you", "thanks", "appreciate it"]):
            return "You're very welcome! Let me know if you need anything else."

        return (
            f"Regarding your query on **{message.strip()}**:\n\n"
            "I have processed your prompt. You can ask for a deep dive, step-by-step breakdown, "
            "code example, image creation, or verification depending on your target goal."
        )
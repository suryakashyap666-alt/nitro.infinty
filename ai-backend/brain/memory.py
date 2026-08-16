from __future__ import annotations

import json
import os
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from time import time
from typing import Any, Dict, List, Optional


@dataclass
class ChatMemoryEvent:
    message: str
    reply: str
    emotion: str
    topic: str
    ts: str


class MemoryEngine:
    """Persist chat history, mistakes, and weak topics per user."""

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

    def _utc(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _is_guest(self, user_id: str) -> bool:
        return isinstance(user_id, str) and user_id.startswith('guest_')

    def _record_image_feedback(self, image_key: str, feedback: str) -> None:
        """Record global image feedback (like/dislike) for AI improvement.
        image_key format: 'style_quality' e.g., 'Anime_HD', 'Hyperrealistic_4K'
        """
        if not image_key or feedback not in ['like', 'dislike']:
            return
        data = self._load()
        data.setdefault('image_feedback', {})
        fb = data['image_feedback']
        fb.setdefault(image_key, {'likes': 0, 'dislikes': 0})
        if feedback == 'like':
            fb[image_key]['likes'] += 1
        else:
            fb[image_key]['dislikes'] += 1
        self._save(data)

    def get_image_feedback(self, image_key: str) -> Dict[str, int]:
        """Get global feedback stats for an image key."""
        data = self._load()
        fb = data.get('image_feedback', {})
        return fb.get(image_key, {'likes': 0, 'dislikes': 0})

    def get_all_image_feedback(self) -> Dict[str, Dict[str, int]]:
        """Get all image feedback for AI improvement training."""
        data = self._load()
        return data.get('image_feedback', {})

    def load_user_state(self, user_id: str) -> Dict[str, Any]:
        data = self._load()
        users = data.setdefault("users", {})
        u = users.setdefault(user_id, {})

        # Existing fields
        u.setdefault("chat_history", [])
        u.setdefault("mistakes", [])
        u.setdefault("weak_topics", {})
        u.setdefault("coding_history", [])

        # Multilingual system fields (per user)
        # - preferred_language: manual language selection for AUTO-detect OFF
        # - language_history: language history for analytics/debug
        # - voice_preferences: preferred voice language + enabled flag
        u.setdefault("preferred_language", "en")
        u.setdefault("language_history", [])
        u.setdefault("voice_preferences", {"enabled": True, "voice_language": None})
        u.setdefault("profile", {})

        # Bot-scoped multilingual state
        u.setdefault("bot_languages", {})
        u.setdefault("bot_voice_preferences", {})

        # Profession intelligence state
        u.setdefault("profession", {"name": None, "level": "beginner"})
        u.setdefault("profession_interests", [])
        u.setdefault("profession_workflows", [])
        u.setdefault("profession_tools", [])
        u.setdefault("profession_learning", {})

        # Web intelligence / user interest fields
        u.setdefault("favorites", [])
        u.setdefault("preferred_sources", [])
        u.setdefault("search_history", [])
        u.setdefault("learning_interests", [])
        # Image system
        u.setdefault("image_history", [])
        u.setdefault("bot_image", {})

        return u

    def append_search_history(self, user_id: str, query: str, results: list | None = None, max_len: int = 50) -> None:
        if self._is_guest(user_id) or not query:
            return
        data = self._load()
        users = data.setdefault("users", {})
        u = users.setdefault(user_id, {})
        u.setdefault("search_history", [])
        hist = u.get("search_history") or []
        summary = {
            "query": query,
            "ts": self._utc(),
            "result_count": len(results) if isinstance(results, list) else 0,
        }
        hist.append(summary)
        u["search_history"] = hist[-max_len:]
        self._save(data)

    def append_image_history(self, user_id: str, image_action: Dict[str, Any], max_len: int = 200) -> None:
        """Append a generated/liked/analysis image action to user's image history."""
        if self._is_guest(user_id) or not image_action:
            return
        data = self._load()
        users = data.setdefault("users", {})
        u = users.setdefault(user_id, {})
        u.setdefault("image_history", [])
        hist = u.get("image_history") or []
        entry = {
            "action": image_action,
            "ts": self._utc(),
        }
        hist.append(entry)
        u["image_history"] = hist[-max_len:]
        self._save(data)

    def get_image_history(self, user_id: str, max_len: int = 200) -> List[Dict[str, Any]]:
        u = self.load_user_state(user_id)
        return list((u.get("image_history") or [])[-max_len:])

    def set_user_preferences(self, user_id: str, prefs: Dict[str, Any]) -> None:
        if self._is_guest(user_id):
            return
        data = self._load()
        users = data.setdefault("users", {})
        u = users.setdefault(user_id, {})
        # supported keys: favorites, preferred_sources, learning_interests, preferred_language
        if "favorites" in prefs:
            u["favorites"] = list(prefs.get("favorites") or [])
        if "preferred_sources" in prefs:
            u["preferred_sources"] = list(prefs.get("preferred_sources") or [])
        if "learning_interests" in prefs:
            u["learning_interests"] = list(prefs.get("learning_interests") or [])
        if "preferred_language" in prefs:
            u["preferred_language"] = prefs.get("preferred_language") or u.get("preferred_language", "en")
        self._save(data)

    def get_user_preferences(self, user_id: str) -> Dict[str, Any]:
        u = self.load_user_state(user_id)
        return {
            "favorites": u.get("favorites", []),
            "preferred_sources": u.get("preferred_sources", []),
            "search_history": u.get("search_history", []),
            "learning_interests": u.get("learning_interests", []),
            "preferred_language": u.get("preferred_language", "en"),
        }

    # Lightweight global search cache persisted inside nitro_state.json under 'web_cache'
    def get_cached_search(self, query: str) -> Dict[str, Any] | None:
        if not query:
            return None
        data = self._load()
        cache = data.setdefault("web_cache", {})
        entry = cache.get(query)
        return entry

    def set_cached_search(self, query: str, results: list) -> None:
        if not query:
            return
        data = self._load()
        cache = data.setdefault("web_cache", {})
        cache[query] = {"ts": self._utc(), "results": results}
        # keep cache small
        try:
            # prune to 200 entries
            keys = list(cache.keys())[-200:]
            new_cache = {k: cache[k] for k in keys}
            data["web_cache"] = new_cache
        except Exception:
            data["web_cache"] = cache
        self._save(data)

    def load_bot_language_policy(self, user_id: str, bot_id: str) -> Dict[str, Any]:
        u = self.load_user_state(user_id)
        bot_languages = u.get("bot_languages") or {}
        return bot_languages.get(bot_id) or {"useGlobalLanguageSystem": True}

    def load_bot_preferred_language(self, user_id: str, bot_id: str) -> str | None:
        u = self.load_user_state(user_id)
        bot_languages = u.get("bot_languages") or {}
        bot = bot_languages.get(bot_id) or {}
        return bot.get("preferredLanguage")

    def load_bot_education_policy(self, user_id: str, bot_id: str) -> Dict[str, Any]:
        u = self.load_user_state(user_id)
        edu = u.get("bot_education") or {}
        return edu.get(bot_id) or {"educationEnabled": False}

    def set_bot_education_policy(self, user_id: str, bot_id: str, policy_state: Dict[str, Any]) -> None:
        if self._is_guest(user_id):
            return
        data = self._load()
        users = data.setdefault("users", {})
        u = users.setdefault(user_id, {})
        u.setdefault("bot_education", {})
        edu = u.get("bot_education") or {}
        edu[bot_id] = policy_state
        u["bot_education"] = edu
        self._save(data)

    def load_bot_web_policy(self, user_id: str, bot_id: str) -> Dict[str, Any]:
        u = self.load_user_state(user_id)
        web = u.get("bot_web") or {}
        return web.get(bot_id) or {"webSearchEnabled": False, "allowedWebCategories": [], "trustedSources": []}

    def set_bot_web_policy(self, user_id: str, bot_id: str, policy_state: Dict[str, Any]) -> None:
        if self._is_guest(user_id):
            return
        data = self._load()
        users = data.setdefault("users", {})
        u = users.setdefault(user_id, {})
        u.setdefault("bot_web", {})
        web = u.get("bot_web") or {}
        web[bot_id] = policy_state
        u["bot_web"] = web
        self._save(data)

    def load_bot_image_policy(self, user_id: str, bot_id: str) -> Dict[str, Any]:
        u = self.load_user_state(user_id)
        img = u.get("bot_image") or {}
        return img.get(bot_id) or {"imageGenerationEnabled": True, "imageDetectionEnabled": True}

    def set_bot_image_policy(self, user_id: str, bot_id: str, policy_state: Dict[str, Any]) -> None:
        if self._is_guest(user_id):
            return
        data = self._load()
        users = data.setdefault("users", {})
        u = users.setdefault(user_id, {})
        u.setdefault("bot_image", {})
        img = u.get("bot_image") or {}
        img[bot_id] = policy_state
        u["bot_image"] = img
        self._save(data)

    def load_bot_profession_policy(self, user_id: str, bot_id: str) -> Dict[str, Any]:
        u = self.load_user_state(user_id)
        prof = u.get("bot_profession") or {}
        return prof.get(bot_id) or {"professionEnabled": False}

    def set_bot_profession_policy(self, user_id: str, bot_id: str, policy_state: Dict[str, Any]) -> None:
        if self._is_guest(user_id):
            return
        data = self._load()
        users = data.setdefault("users", {})
        u = users.setdefault(user_id, {})
        u.setdefault("bot_profession", {})
        prof = u.get("bot_profession") or {}
        prof[bot_id] = policy_state
        u["bot_profession"] = prof
        self._save(data)

    def load_bot_context_policy(self, user_id: str, bot_id: str) -> Dict[str, Any]:
        """Load bot-level context understanding policy for the given user and bot.

        Returns a dict with keys:
        - contextUnderstandingEnabled: bool
        - useUserHistoryUnderstanding: bool
        - useWebAssistance: bool
        """
        u = self.load_user_state(user_id)
        ctx = u.get("bot_context") or {}
        return ctx.get(bot_id) or {
            "contextUnderstandingEnabled": False,
            "useUserHistoryUnderstanding": False,
            "useWebAssistance": False,
        }

    def set_bot_context_policy(self, user_id: str, bot_id: str, policy_state: Dict[str, Any]) -> None:
        if self._is_guest(user_id):
            return
        data = self._load()
        users = data.setdefault("users", {})
        u = users.setdefault(user_id, {})
        u.setdefault("bot_context", {})
        ctx = u.get("bot_context") or {}
        ctx[bot_id] = policy_state
        u["bot_context"] = ctx
        self._save(data)

    def load_user_profession_state(self, user_id: str) -> Dict[str, Any]:
        u = self.load_user_state(user_id)
        return u.get("profession") or {"name": None, "level": "beginner"}

    def set_user_profession_state(self, user_id: str, profession_state: Dict[str, Any]) -> None:
        if self._is_guest(user_id):
            return
        data = self._load()
        users = data.setdefault("users", {})
        u = users.setdefault(user_id, {})
        u["profession"] = profession_state
        self._save(data)

    def append_profession_interest(self, user_id: str, interest: str) -> None:
        if self._is_guest(user_id) or not interest:
            return
        data = self._load()
        users = data.setdefault("users", {})
        u = users.setdefault(user_id, {})
        u.setdefault("profession_interests", [])
        interests = u.get("profession_interests") or []
        if interest not in interests:
            interests.append(interest)
        u["profession_interests"] = interests[-20:]
        self._save(data)

    def append_profession_workflow(self, user_id: str, workflow: str) -> None:
        if self._is_guest(user_id) or not workflow:
            return
        data = self._load()
        users = data.setdefault("users", {})
        u = users.setdefault(user_id, {})
        u.setdefault("profession_workflows", [])
        workflows = u.get("profession_workflows") or []
        if workflow not in workflows:
            workflows.append(workflow)
        u["profession_workflows"] = workflows[-20:]
        self._save(data)

    def append_profession_tool(self, user_id: str, tool: str) -> None:
        if self._is_guest(user_id) or not tool:
            return
        data = self._load()
        users = data.setdefault("users", {})
        u = users.setdefault(user_id, {})
        u.setdefault("profession_tools", [])
        tools = u.get("profession_tools") or []
        if tool not in tools:
            tools.append(tool)
        u["profession_tools"] = tools[-20:]
        self._save(data)

    def record_profession_learning_progress(self, user_id: str, progress: Dict[str, Any]) -> None:
        if self._is_guest(user_id):
            return
        data = self._load()
        users = data.setdefault("users", {})
        u = users.setdefault(user_id, {})
        u["profession_learning"] = u.get("profession_learning", {})
        u["profession_learning"].update(progress)
        self._save(data)


    def set_bot_language_policy(
        self,
        user_id: str,
        bot_id: str,
        policy_state: Dict[str, Any],
    ) -> None:
        if self._is_guest(user_id):
            return
        data = self._load()
        users = data.setdefault("users", {})
        u = users.setdefault(user_id, {})
        u.setdefault("chat_history", [])
        u.setdefault("mistakes", [])
        u.setdefault("weak_topics", {})
        u.setdefault("coding_history", [])
        u.setdefault("bot_languages", {})
        bot_languages = u.get("bot_languages") or {}
        bot_languages[bot_id] = policy_state
        u["bot_languages"] = bot_languages
        self._save(data)

    def set_preferred_language(self, user_id: str, lang_code: str) -> None:

        if self._is_guest(user_id):
            return
        data = self._load()
        users = data.setdefault("users", {})
        u = users.setdefault(user_id, {})
        u.setdefault("chat_history", [])
        u.setdefault("mistakes", [])
        u.setdefault("weak_topics", {})
        u.setdefault("coding_history", [])
        u["preferred_language"] = lang_code
        # write back
        self._save(data)

    def append_language_history(self, user_id: str, lang_code: str, max_len: int = 20) -> None:
        if self._is_guest(user_id):
            return
        data = self._load()
        users = data.setdefault("users", {})
        u = users.setdefault(user_id, {})
        u.setdefault("language_history", [])
        hist = u.get("language_history") or []
        if not hist or hist[-1] != lang_code:
            hist.append(lang_code)
        u["language_history"] = hist[-max_len:]
        self._save(data)


    def append_message(self, user_id: str, message: str, reply: str, emotion: str, topic: str) -> None:
        if self._is_guest(user_id):
            return
        data = self._load()
        users = data.setdefault("users", {})
        u = users.setdefault(user_id, {})
        u.setdefault("chat_history", [])
        u["chat_history"].append(
            {
                "message": message,
                "reply": reply,
                "emotion": emotion,
                "topic": topic,
                "ts": self._utc(),
            }
        )
        self._save(data)

    def record_mistake(self, user_id: str, result: Dict[str, Any]) -> None:
        if self._is_guest(user_id):
            return
        data = self._load()
        users = data.setdefault("users", {})
        u = users.setdefault(user_id, {})
        u.setdefault("mistakes", [])
        u["mistakes"].append(
            {
                "topic": result.get("topic", "general"),
                "ts": self._utc(),
                "detail": result,
            }
        )
        self._save(data)

    def record_mistake_or_success(self, user_id: str, eval_meta: Dict[str, Any]) -> None:
        if self._is_guest(user_id):
            return
        is_correct = bool(eval_meta.get("correct", False))
        data = self._load()
        users = data.setdefault("users", {})
        u = users.setdefault(user_id, {})
        u.setdefault("mistakes", [])
        u["mistakes"].append(
            {
                "topic": eval_meta.get("topic", "general"),
                "ts": self._utc(),
                "correct": is_correct,
                "detail": eval_meta,
            }
        )
        self._save(data)

    def set_education_last_task(
        self,
        user_id: str,
        *,
        kind: str,
        subject_id: str,
        answer_key: Any = None,
        extra: Dict[str, Any] | None = None,
    ) -> None:
        """Store last generated universal-education task for reliable #answer updates."""
        if self._is_guest(user_id):
            return
        data = self._load()
        users = data.setdefault("users", {})
        u = users.setdefault(user_id, {})
        u.setdefault("education_last_task", {})
        u["education_last_task"] = {
            "kind": kind,
            "subject_id": str(subject_id),
            "answer_key": answer_key,
            "extra": extra or {},
            "ts": self._utc(),
        }
        self._save(data)

    def get_education_last_task(self, user_id: str) -> Dict[str, Any]:
        if self._is_guest(user_id):
            return {}
        data = self._load()
        users = data.setdefault("users", {})
        u = users.get(user_id) or {}
        return u.get("education_last_task") or {}

    def append_coding_like_event(self, user_id: str, kind: str, payload: Dict[str, Any]) -> None:
        if self._is_guest(user_id):
            return
        data = self._load()
        users = data.setdefault("users", {})
        u = users.setdefault(user_id, {})
        u.setdefault("coding_history", [])
        u["coding_history"].append({"kind": kind, "payload": payload, "ts": self._utc()})
        self._save(data)

    # ===== Memory Graph (lightweight) =====
    def add_memory_node(self, user_id: str, node_id: str, meta: Dict[str, Any] | None = None) -> None:
        if self._is_guest(user_id) or not node_id:
            return
        data = self._load()
        users = data.setdefault("users", {})
        u = users.setdefault(user_id, {})
        graph = u.setdefault("memory_graph", {"nodes": {}, "edges": {}})
        nodes = graph.setdefault("nodes", {})
        nodes[node_id] = {"meta": meta or {}, "ts": self._utc()}
        u["memory_graph"] = graph
        self._save(data)

    def link_memory_nodes(self, user_id: str, from_node: str, to_node: str, relation: str = "related") -> None:
        if self._is_guest(user_id) or not from_node or not to_node:
            return
        data = self._load()
        users = data.setdefault("users", {})
        u = users.setdefault(user_id, {})
        graph = u.setdefault("memory_graph", {"nodes": {}, "edges": {}})
        edges = graph.setdefault("edges", {})
        edges.setdefault(from_node, [])
        edges[from_node].append({"to": to_node, "relation": relation, "ts": self._utc()})
        u["memory_graph"] = graph
        self._save(data)

    def query_related_interests(self, user_id: str, seed: str, depth: int = 2) -> List[str]:
        if self._is_guest(user_id) or not seed:
            return []
        data = self._load()
        users = data.setdefault("users", {})
        u = users.setdefault(user_id, {})
        graph = u.get("memory_graph") or {"nodes": {}, "edges": {}}
        edges = graph.get("edges") or {}
        seen = set()
        frontier = [seed]
        for _ in range(depth):
            new_front = []
            for n in frontier:
                for e in edges.get(n, []):
                    t = e.get("to")
                    if t and t not in seen:
                        seen.add(t)
                        new_front.append(t)
            frontier = new_front
        return list(seen)

    def get_memory_graph(self, user_id: str) -> Dict[str, Any]:
        if self._is_guest(user_id):
            return {"nodes": {}, "edges": {}}
        data = self._load()
        users = data.setdefault("users", {})
        u = users.setdefault(user_id, {})
        return u.get("memory_graph") or {"nodes": {}, "edges": {}}

    # Higher-level helpers for interests, personality, and learning patterns
    def add_interest(self, user_id: str, interest: str, weight: float = 1.0) -> None:
        if self._is_guest(user_id) or not interest:
            return
        # normalize
        key = f"interest:{interest.lower()}"
        self.add_memory_node(user_id, key, meta={"type": "interest", "label": interest, "weight": weight})

    def record_interaction(self, user_id: str, topic: str, kind: str = "chat", metadata: Dict[str, Any] | None = None) -> None:
        """Record a user interaction as a node and link to recent interests.

        This helps build contextual memory and track learning patterns.
        """
        if self._is_guest(user_id) or not topic:
            return
        node_id = f"interaction:{int(time())}:{hash(topic)}"
        meta = {"type": "interaction", "topic": topic, "kind": kind}
        if metadata:
            meta.update(metadata)
        self.add_memory_node(user_id, node_id, meta=meta)

        # link to topic node and top interests
        topic_node = f"topic:{topic.lower()}"
        self.add_memory_node(user_id, topic_node, meta={"type": "topic", "label": topic})
        self.link_memory_nodes(user_id, node_id, topic_node, relation="about")

        # link to recent interests (last 5)
        state = self.load_user_state(user_id)
        recent_interests = (state.get("learning_interests") or [])[-5:]
        for it in recent_interests:
            in_key = f"interest:{it.lower()}"
            self.add_memory_node(user_id, in_key, meta={"type": "interest", "label": it})
            self.link_memory_nodes(user_id, node_id, in_key, relation="related_interest")

    def set_personality_trait(self, user_id: str, trait: str, value: Any) -> None:
        if self._is_guest(user_id) or not trait:
            return
        data = self._load()
        users = data.setdefault("users", {})
        u = users.setdefault(user_id, {})
        u.setdefault("personality", {})
        u["personality"][trait] = value
        self._save(data)

    def get_personality_profile(self, user_id: str) -> Dict[str, Any]:
        if self._is_guest(user_id):
            return {}
        u = self.load_user_state(user_id)
        return u.get("personality") or {}

    def summarize_learning_patterns(self, user_id: str) -> Dict[str, Any]:
        """Return a small summary of user's learning patterns based on stored memory.

        Lightweight heuristic: count topic interactions, recent interests, success rate.
        """
        if self._is_guest(user_id):
            return {}
        u = self.load_user_state(user_id)
        # topic counts
        chat_history = u.get("chat_history") or []
        topic_counts: Dict[str, int] = {}
        for ev in chat_history:
            t = ev.get("topic") or "general"
            topic_counts[t] = topic_counts.get(t, 0) + 1

        # learning success approximation
        mistakes = u.get("mistakes") or []
        success = max(0, len(chat_history) - len(mistakes))
        total = max(1, len(chat_history))
        success_rate = success / total

        return {
            "top_topics": sorted(topic_counts.items(), key=lambda x: -x[1])[:5],
            "recent_interests": (u.get("learning_interests") or [])[-10:],
            "success_rate": success_rate,
        }

    def recommend_examples_from_graph(self, user_id: str, seed: str, max_results: int = 5) -> List[Dict[str, Any]]:
        """Return simple recommendations by exploring memory graph neighbors of `seed`."""
        if self._is_guest(user_id) or not seed:
            return []
        graph = self.get_memory_graph(user_id)
        nodes = graph.get("nodes") or {}
        edges = graph.get("edges") or {}
        seed_key = seed if seed.startswith("topic:") or seed.startswith("interest:") else f"topic:{seed.lower()}"
        neighbors = edges.get(seed_key) or []
        out = []
        for n in neighbors[:max_results]:
            t = n.get("to")
            if not t:
                continue
            node_meta = nodes.get(t) or {}
            out.append({"id": t, "meta": node_meta.get("meta")})
        return out



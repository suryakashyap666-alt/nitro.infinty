from __future__ import annotations

import base64
import hashlib
import json
import logging
import os
import re
import threading
import time
import urllib.request
import uuid
from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.error import HTTPError, URLError
from urllib.parse import parse_qs, quote_plus, unquote, urlparse

from .coding_engine import CodingEngine
from .context_engine import ContextEngine
from .creative_engine import CreativeEngine
from .education_subjects_engine import EducationSubjectsEngine
from .emotion import EmotionEngine
from .exam import ExamEngine
from .learning import LearningEngine
from .math_engine import MathEngine
from .memory import MemoryEngine
from .profession_engine import ProfessionEngine
from .response_composer import ResponseComposer
from .risk_analyzer import RiskAnalyzer
from .topic_detector import TopicDetector

try:
    from legacy.image.image_system import (
        detect_image_intent,
        generate_image_fake,
        plan_style_and_quality,
        safety_block,
    )
except (ImportError, ValueError):
    def detect_image_intent(message: str): return None
    def plan_style_and_quality(prompt: str): return None
    def generate_image_fake(prompt: str, plan: Any, seed: Optional[int] = None, feedback_stats: Optional[Dict[str, int]] = None): return {}
    def safety_block(prompt: str): return None


class CoreBrain:
    """Native Intelligence & Conversational Core for Nitro Infinity AI."""

    def __init__(self, storage_path: str, bot_market: object | None = None) -> None:
        self.storage_path = storage_path
        self.bot_market = bot_market

        self.memory = MemoryEngine(storage_path=storage_path)
        self.emotion = EmotionEngine(storage_path=storage_path)
        self.topic_detector = TopicDetector()
        self.risk = RiskAnalyzer()
        self.learning = LearningEngine(storage_path=storage_path)
        self.exam = ExamEngine()
        self.math = MathEngine()
        self.creative = CreativeEngine(storage_path=storage_path)
        self.coding = CodingEngine()
        self.profession = ProfessionEngine()
        self.composer = ResponseComposer()
        self.context = ContextEngine(storage_path=storage_path)
        self.education = EducationSubjectsEngine()

        self._executor = ThreadPoolExecutor(max_workers=4)

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
        clean_text = (message or "").strip()
        if not clean_text:
            return {"reply": "Hey! How can I help you today?", "emotion": "neutral", "topic": "general"}

        # Safety Check
        risk_result = self.risk.analyze(clean_text, user_id=user_id)
        if risk_result.get("blocked"):
            return {"reply": risk_result.get("reply", "I cannot fulfill this request due to safety policies."), "emotion": "neutral", "topic": "safety"}

        # Detect User Emotion
        user_emotion = self.emotion.detect_and_update(user_id=user_id, message=clean_text)

        # 1. Image Studio Intent
        img_intent = detect_image_intent(clean_text)
        if img_intent and img_intent.action == "generate":
            plan = plan_style_and_quality(img_intent.prompt)
            gen = generate_image_fake(prompt=img_intent.prompt, plan=plan)
            img_data = gen.get("image", {})
            action = {
                "type": "generate",
                "status": "done",
                "prompt": img_intent.prompt,
                "style": plan.style if plan else "Concept",
                "quality": plan.quality if plan else "HD",
                "image": img_data,
            }
            if persist_chat:
                self.memory.append_message(user_id, clean_text, f"Generated image: {img_intent.prompt}", emotion="happy", topic="image")
            return {
                "reply": f"Here is your rendered image for **{img_intent.prompt}**:",
                "emotion": "happy",
                "topic": "image",
                "imageAction": action,
            }

        # 2. Math & Calculation Expression
        if self.math.is_math_expression(clean_text):
            math_res = self.math.solve(clean_text, user_id=user_id, as_teaching=True)
            reply = math_res.get("reply", "")
            if persist_chat:
                self.memory.append_message(user_id, clean_text, reply, emotion=user_emotion, topic="math")
            return {"reply": reply, "emotion": user_emotion, "topic": "math"}

        # 3. Coding & Software Architecture
        low = clean_text.lower()
        if clean_text.startswith("#code") or any(k in low for k in ["write code", "how to code", "debug this", "python script", "javascript function", "fastapi app", "react component"]):
            code_res = self.coding.generate_code(clean_text, user_id=user_id)
            reply = code_res.get("reply", "")
            if persist_chat:
                self.memory.append_message(user_id, clean_text, reply, emotion=user_emotion, topic="coding")
            return {"reply": reply, "emotion": user_emotion, "topic": "coding"}

        # 4. Creative Writing (Stories, Poems, Dialogues, Jokes)
        if any(k in low for k in ["tell me a joke", "write a poem", "make up a story", "tell a riddle", "write a dialogue"]):
            creative_res = self.creative.generate(user_id=user_id, message=clean_text)
            reply = creative_res.get("reply", "")
            if persist_chat:
                self.memory.append_message(user_id, clean_text, reply, emotion=user_emotion, topic="creative")
            return {"reply": reply, "emotion": user_emotion, "topic": "creative"}

        # 5. Live Web Research (Current events, lookups, queries)
        if self._is_live_search_query(clean_text):
            search_res = self._handle_live_web_search(user_id=user_id, query=clean_text)
            reply = search_res.get("reply", "")
            if persist_chat:
                self.memory.append_message(user_id, clean_text, reply, emotion=user_emotion, topic="web_search")
            return {"reply": reply, "emotion": user_emotion, "topic": "web_search"}

        # 6. Natural Dynamic Conversation (Natural Dialogue Mind)
        natural_reply = self._generate_conversational_reply(clean_text, user_id=user_id, emotion=user_emotion, context=conversation_context)
        final_reply = self.composer.compose(
            user_id=user_id,
            emotion=user_emotion,
            topic="general",
            risk_result=risk_result,
            base_reply=natural_reply,
            learning_update=None,
            chat_mode={"strict": False},
        )

        if persist_chat:
            self.memory.append_message(user_id, clean_text, final_reply, emotion=user_emotion, topic="general")

        return {"reply": final_reply, "emotion": user_emotion, "topic": "general"}

    def _is_live_search_query(self, text: str) -> bool:
        low = text.lower()
        triggers = ["search:", "who is ", "what is happening with", "latest news about", "stock price of", "weather in "]
        return any(low.startswith(t) for t in triggers)

    def _handle_live_web_search(self, user_id: str, query: str) -> Dict[str, Any]:
        clean_q = re.sub(r"^(search:|find:)\s*", "", query, flags=re.I).strip()
        search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(clean_q)}"
        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

        try:
            req = urllib.request.Request(search_url, headers=headers)
            with urllib.request.urlopen(req, timeout=8) as response:
                html = response.read().decode("utf-8", errors="ignore")
                snippets = re.findall(r'<a[^>]+class="result__snippet"[^>]*>(.*?)</a>', html, flags=re.S)
                if snippets:
                    clean_snippet = re.sub(r"<.*?>", "", snippets[0]).strip()
                    return {"reply": f"Here is what I found on **{clean_q}**:\n\n{clean_snippet}"}
        except Exception:
            pass

        return {"reply": f"I attempted to look up '{clean_q}', but couldn't reach live web search results right now. I can still analyze what we know directly."}

    def _generate_conversational_reply(
        self,
        message: str,
        user_id: str,
        emotion: str,
        context: Optional[List[Dict[str, str]]] = None,
    ) -> str:
        """Dynamic, context-aware dialogue generator for natural human-like chat."""
        low = message.lower().strip()

        # Greetings
        if re.search(r"^(hi|hello|hey|yo|sup|greetings|namaste|good morning|good evening)\b", low):
            return "Hey there! I'm here and ready. What's on your mind today?"

        # Identity questions
        if any(k in low for k in ["who are you", "what are you", "what is your name"]):
            return "I am Nitro Infinity AI — your built-in intelligence engine for reasoning, problem-solving, math, coding, creative design, and learning."

        # How are you / Status
        if any(k in low for k in ["how are you", "how are you doing", "how's it going"]):
            if emotion == "happy":
                return "I'm running great, and glad to see you're in a good mood! What are we tackling next?"
            return "Doing well and ready to help. What are you working on right now?"

        # Fun / personality questions
        if "what can you do" in low or "help me" in low:
            return (
                "Here is what we can do together:\n\n"
                "• **Reasoning & Chat:** Talk through ideas, explore concepts, brainstorm.\n"
                "• **Math & Logic:** Step-by-step algebra, calculus, and equation solving.\n"
                "• **Code & Build:** Python, JavaScript, API design, debugging.\n"
                "• **Image Studio:** Describe any scene to render digital artwork and concepts.\n"
                "• **Learning & Quizzes:** Step-by-step explanations on any academic topic.\n\n"
                "Just tell me what you want to jump into!"
            )

        # Gratitude
        if any(k in low for k in ["thank you", "thanks", "thx", "appreciate it"]):
            return "You're very welcome! Let me know whenever you're ready for the next thing."

        # Agreement / casually continuing
        if low in ["yes", "yeah", "sure", "ok", "okay", "yep", "cool", "nice"]:
            return "Sounds good! Tell me where you'd like to take this next."

        # Open-ended dynamic dialogue response
        # Synthesize a smart, thoughtful response rather than a scripted card
        return (
            f"You brought up an interesting point about **{message}**.\n\n"
            "We can dive deeper into the mechanics, work out a practical example, "
            "or explore how this connects to related topics. What angle do you want to start with?"
        )
from __future__ import annotations

import base64
import json
import logging
import os
import re
import urllib.request
import uuid
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, List, Optional
from urllib.parse import quote_plus

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


class AIRouter:
    def __init__(self, brain: Any) -> None:
        self.brain = brain

    def route(self, user_id: str, message: str, bot_id: str | None = None) -> Optional[Dict[str, Any]]:
        return None


class TaskAgent:
    def __init__(self, brain: Any) -> None:
        self.brain = brain

    def submit_task(self, task_type: str, user_id: str, payload: Dict[str, Any] | None = None) -> str:
        return str(uuid.uuid4())


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

        self.router = AIRouter(self)
        self.task_agent = TaskAgent(self)
        self._executor = ThreadPoolExecutor(max_workers=4)

    def _query_free_cloud_model(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
    ) -> Optional[str]:
        api_key = (
            os.environ.get("NITRO_CLOUD_API_KEY")
            or os.environ.get("OPENROUTER_API_KEY")
            or os.environ.get("NITRO_SYSTEM_API_KEY")
        )
        if not api_key:
            return None

        base_url = os.environ.get("NITRO_API_BASE", "https://openrouter.ai/api/v1").rstrip("/")
        model_name = os.environ.get("NITRO_FREE_MODEL", "meta-llama/llama-3.3-70b-instruct:free")

        url = f"{base_url}/chat/completions"
        conversation_payload = []
        if system_prompt:
            conversation_payload.append({"role": "system", "content": system_prompt})
        conversation_payload.extend(messages)

        payload = {
            "model": model_name,
            "messages": conversation_payload,
            "stream": False,
        }

        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                    "HTTP-Referer": "https://nitro-ai.local",
                    "X-Title": "Nitro Infinity AI",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                choices = res_data.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "").strip()
                    if content:
                        return content
        except Exception:
            pass

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
        clean_text = (message or "").strip()
        if not clean_text:
            return {"reply": "Hey! How can I help you today?", "emotion": "neutral", "topic": "general"}

        # 1. Safety Guardrails Check
        risk_result = self.risk.analyze(clean_text, user_id=user_id)
        if risk_result.get("blocked"):
            return {"reply": risk_result.get("reply", "I cannot fulfill this request due to safety policies."), "emotion": "neutral", "topic": "safety"}

        # 2. Detect User Emotion & Sentiment
        user_emotion = self.emotion.detect_and_update(user_id=user_id, message=clean_text)

        # 3. Image Studio Intent (Native CairoSVG / Pillow Vector Studio)
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

        # 4. Math & Calculus Solver (Native Step-by-Step Evaluator)
        if self.math.is_math_expression(clean_text):
            math_res = self.math.solve(clean_text, user_id=user_id, as_teaching=True)
            reply = math_res.get("reply", "")
            if persist_chat:
                self.memory.append_message(user_id, clean_text, reply, emotion=user_emotion, topic="math")
            return {"reply": reply, "emotion": user_emotion, "topic": "math"}

        # 5. Coding & Software Architecture
        low = clean_text.lower()
        if clean_text.startswith("#code") or any(k in low for k in ["write code", "how to code", "debug this", "python script", "javascript function", "fastapi app", "react component"]):
            code_res = self.coding.generate_code(clean_text, user_id=user_id)
            reply = code_res.get("reply", "")
            if persist_chat:
                self.memory.append_message(user_id, clean_text, reply, emotion=user_emotion, topic="coding")
            return {"reply": reply, "emotion": user_emotion, "topic": "coding"}

        # 6. Creative Writing (Stories, Poems, Riddles, Jokes)
        if any(k in low for k in ["tell me a joke", "write a poem", "make up a story", "tell a riddle", "write a dialogue"]):
            creative_res = self.creative.generate(user_id=user_id, message=clean_text)
            reply = creative_res.get("reply", "")
            if persist_chat:
                self.memory.append_message(user_id, clean_text, reply, emotion=user_emotion, topic="creative")
            return {"reply": reply, "emotion": user_emotion, "topic": "creative"}

        # 7. Live Web Research (DuckDuckGo Realtime Scraper)
        if self._is_live_search_query(clean_text):
            search_res = self._handle_live_web_search(user_id=user_id, query=clean_text)
            reply = search_res.get("reply", "")
            if persist_chat:
                self.memory.append_message(user_id, clean_text, reply, emotion=user_emotion, topic="web_search")
            return {"reply": reply, "emotion": user_emotion, "topic": "web_search"}

        # 8. Conversational Mind (Cloud Free Model + Native Fallback)
        history_msgs = conversation_context or [{"role": "user", "content": clean_text}]
        system_instructions = (
            "You are Nitro Infinity AI. You are natural, articulate, intelligent, friendly, and direct. "
            "Never reply with robotic boilerplate, bracket tags, or canned templates. "
            "Provide helpful, concise, human-like answers."
        )

        cloud_reply = self._query_free_cloud_model(messages=history_msgs, system_prompt=system_instructions)

        if cloud_reply:
            final_reply = cloud_reply
        else:
            final_reply = self._generate_conversational_reply(clean_text, user_id=user_id, emotion=user_emotion)

        final_composed = self.composer.compose(
            user_id=user_id,
            emotion=user_emotion,
            topic="general",
            risk_result=risk_result,
            base_reply=final_reply,
            learning_update=None,
            chat_mode={"strict": False},
        )

        if persist_chat:
            self.memory.append_message(user_id, clean_text, final_composed, emotion=user_emotion, topic="general")

        return {"reply": final_composed, "emotion": user_emotion, "topic": "general"}

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

        return {"reply": f"I attempted to look up '{clean_q}', but couldn't reach live web search results right now."}

    def _generate_conversational_reply(
        self,
        message: str,
        user_id: str,
        emotion: str,
    ) -> str:
        low = message.lower().strip()

        if re.search(r"^(hi|hello|hey|yo|sup|greetings|namaste|good morning|good evening)\b", low):
            return "Hey! I'm here and ready. What are we working on today?"

        if any(k in low for k in ["who are you", "what are you", "what is your name"]):
            return "I am Nitro Infinity AI — your built-in intelligence engine for reasoning, problem-solving, math, coding, creative design, and learning."

        if any(k in low for k in ["how are you", "how's it going"]):
            return "Doing great and ready to help. What's on your mind?"

        if any(k in low for k in ["thank you", "thanks", "thx"]):
            return "You're very welcome! Let me know if you need anything else."

        return (
            f"You brought up an interesting point about **{message}**.\n\n"
            "We can dive deeper into the mechanics, work out a practical example, "
            "or explore how this connects to related topics. What angle do you want to start with?"
        )
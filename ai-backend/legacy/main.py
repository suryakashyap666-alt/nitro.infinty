from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict
import threading
import logging
import uvicorn

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .brain.core import CoreBrain
from .bots_engine import BotMarketplaceEngine, filter_bots
from .bots_logic import create_bot_reply

# Puzzle image endpoint
from .puzzle.puzzle_images_api import router as puzzle_images_router

# Multimodal image endpoints (generation + analysis)
from .image.image_api import router as image_router
from .image.image_system import detect_image_intent, plan_style_and_quality, generate_image_fake, analyze_image_fake, safety_block

# Multilingual system
from .language import detect_language, get_supported_languages_list, get_speech_lang
from .nitro_voice import synthesize_to_base64 as nitro_synthesize_to_base64




# Note: bots endpoints are integrated directly here (no separate router) to avoid breaking existing app setup.



from .models import (

    ChatRequest,
    ChatResponse,
    HistoryResponse,
    SaraswatiLoginRequest,
    SaraswatiLoginResponse,
    AuthVerifyResponse,
)


def _utc_timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def _ensure_data_dir(data_dir: str | None = None) -> str:
    if data_dir:
        data_dir = os.path.abspath(data_dir)
    else:
        base = os.path.dirname(__file__)
        data_dir = os.path.join(base, "data")
    os.makedirs(data_dir, exist_ok=True)
    return data_dir


def _parse_env_int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, str(default)) or default)
    except Exception:
        return default


def _load_saraswati_accounts() -> Dict[str, Any]:
    path = os.path.join(DATA_DIR, "saraswati_accounts.json")
    if not os.path.exists(path):
        return {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _validate_saraswati_account(account_id: str, password: str) -> Dict[str, Any] | None:
    accounts = _load_saraswati_accounts()
    account = accounts.get(account_id)
    if not account:
        return None
    if account.get("password") != password:
        return None
    return account


def _validate_saraswati_external(account_id: str, password: str) -> Dict[str, Any] | None:
    external_url = os.environ.get("SARASWATI_API_URL")
    if not external_url:
        return None

    payload = json.dumps({"account_id": account_id, "password": password}).encode("utf-8")
    request = urllib.request.Request(
        external_url,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=12) as response:
            body = json.loads(response.read().decode("utf-8"))
            if not isinstance(body, dict) or not body.get("success"):
                return None
            return {
                "display_name": body.get("display_name", account_id),
                "email": body.get("email", ""),
                "external_id": body.get("user_id", account_id),
            }
    except Exception:
        return None


JWT_SECRET = os.environ.get("NITRO_JWT_SECRET", "nitro_ai_secret_2026").encode("utf-8")
JWT_EXPIRATION_SECONDS = 60 * 60 * 24 * 7


def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _base64url_decode(data: str) -> bytes:
    padding = '=' * (-len(data) % 4)
    return base64.urlsafe_b64decode(data + padding)


def _sign_jwt(header_b64: str, payload_b64: str) -> str:
    message = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(JWT_SECRET, message, hashlib.sha256).digest()
    return _base64url_encode(signature)


def _generate_auth_token(claims: Dict[str, Any], expires_in: int = JWT_EXPIRATION_SECONDS) -> str:
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {**claims, "exp": int(time.time()) + expires_in}
    header_b64 = _base64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_b64 = _base64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signature = _sign_jwt(header_b64, payload_b64)
    return f"{header_b64}.{payload_b64}.{signature}"


def _decode_auth_token(token: str) -> Dict[str, Any] | None:
    try:
        header_b64, payload_b64, signature = token.split('.')
    except ValueError:
        return None
    expected = _sign_jwt(header_b64, payload_b64)
    if not hmac.compare_digest(signature, expected):
        return None
    try:
        payload_json = _base64url_decode(payload_b64).decode("utf-8")
        payload = json.loads(payload_json)
    except Exception:
        return None
    exp = payload.get("exp")
    if not isinstance(exp, (int, float)) or time.time() > float(exp):
        return None
    return payload


def _get_auth_token_from_request(request: Request) -> str | None:
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth.split(" ", 1)[1].strip()
    return None


def _save_user_profile(user_id: str, profile: Dict[str, Any]) -> None:
    data = BRAIN.memory._load()
    users = data.setdefault("users", {})
    u = users.setdefault(user_id, {})
    u.setdefault("profile", {})
    u["profile"].update(profile)
    u["profile"]["last_login"] = _utc_timestamp()
    u["profile"]["provider"] = profile.get("provider", u["profile"].get("provider", "saraswati"))
    u["profile"]["display_name"] = profile.get("display_name", u["profile"].get("display_name", user_id))
    if "email" in profile:
        u["profile"]["email"] = profile.get("email", u["profile"].get("email", ""))
    BRAIN.memory._save(data)


def _load_user_profile(user_id: str) -> Dict[str, Any] | None:
    state = BRAIN.memory.load_user_state(user_id)
    profile = state.get("profile") or {}
    if not profile:
        return None
    return {"user_id": user_id, **profile}


app = FastAPI(title="Nitro Infinity AI")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_BUILD_DIR = PROJECT_ROOT / "frontend" / "build"

app.add_middleware(

    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_DIR = _ensure_data_dir(os.environ.get("NITRO_DATA_DIR"))
BOT_MARKET = BotMarketplaceEngine(storage_path=os.path.join(DATA_DIR, "nitro_state.json"))
BOT_MARKET.ensure_default_bots()
BRAIN = CoreBrain(storage_path=os.path.join(DATA_DIR, "nitro_state.json"), bot_market=BOT_MARKET)


app.include_router(puzzle_images_router)
app.include_router(image_router)

if FRONTEND_BUILD_DIR.exists() and (FRONTEND_BUILD_DIR / "static").exists():
    app.mount("/static", StaticFiles(directory=str(FRONTEND_BUILD_DIR / "static")), name="static")

    @app.get("/")
    def index() -> Response:
        index_file = FRONTEND_BUILD_DIR / "index.html"
        if index_file.exists():
            return Response(content=index_file.read_text(encoding="utf-8"), media_type="text/html")
        raise HTTPException(status_code=404, detail="Frontend build not found")

    @app.get("/{full_path:path}")
    def catch_all(full_path: str) -> Response:
        index_file = FRONTEND_BUILD_DIR / "index.html"
        if index_file.exists() and full_path and not full_path.startswith("api/"):
            return Response(content=index_file.read_text(encoding="utf-8"), media_type="text/html")
        raise HTTPException(status_code=404, detail="Not found")
else:
    logging.getLogger(__name__).warning(
        "Frontend build missing or incomplete at %s; static routes disabled.",
        FRONTEND_BUILD_DIR,
    )




















@app.post("/chat", response_model=ChatResponse)

def chat(req: ChatRequest) -> ChatResponse:
    # Use a client-side detected language hint if provided, else server-detect.
    detected_lang = str(req.detected_language or "").strip().lower() or detect_language(req.message)

    # Optional bot_id enables bot language policy.
    bot_id = getattr(req, "bot_id", None)

    # --- Multimodal image intent routing (generation + analysis) ---
    intent = detect_image_intent(req.message)
    if intent:
        prompt = str(intent.prompt or "")
        block_reason = safety_block(prompt)
        if block_reason:
            # Non-breaking: keep ChatResponse schema.
            reply = f"[Safety] Image request blocked: {block_reason}."
            return ChatResponse(
                reply=reply,
                timestamp=_utc_timestamp(),
                emotion="neutral",
                topic="image",
                detected_language=detected_lang,
            )

        try:
            if intent.action == "generate":
                plan = plan_style_and_quality(prompt)
                # Get feedback stats to improve generation
                image_key = f"{plan.style}_{plan.quality}".replace(" ", "_")
                feedback = BRAIN.memory.get_image_feedback(image_key)
                gen = generate_image_fake(prompt=prompt, plan=plan, feedback_stats=feedback)
                action = {
                    "type": "generate",
                    "status": "done",
                    "prompt": prompt,
                    "style": gen.get("plan", {}).get("style"),
                    "quality": gen.get("plan", {}).get("quality"),
                    "aspect": gen.get("plan", {}).get("aspect"),
                    "image": gen.get("image"),
                }
                reply = "Generated image (" + str(action.get('style') or 'style') + " • " + str(action.get('quality') or 'HD') + ")."
                return ChatResponse(
                    reply=reply,
                    timestamp=_utc_timestamp(),
                    emotion="neutral",
                    topic="image",
                    detected_language=detected_lang,
                )

            if intent.action == "analyze":
                # In chat mode we can't accept an uploaded file; analysis is supported via /image/analyze.
                # We still respond with guidance.
                reply = "To analyze an image, please upload an image and ask: 'tell me if this is AI made or human made'."
                return ChatResponse(
                    reply=reply,
                    timestamp=_utc_timestamp(),
                    emotion="neutral",
                    topic="image",
                    detected_language=detected_lang,
                )

        except Exception:
            # fall back to normal chat
            pass

    result = BRAIN.handle_message(
        user_id=req.user_id,
        message=req.message,
        persist_chat=not req.guest_mode,
        bot_id=bot_id,
        incoming_language=detected_lang,
    )
    return ChatResponse(
        reply=result["reply"],
        timestamp=_utc_timestamp(),
        emotion=result["emotion"],
        topic=result["topic"],
        detected_language=detected_lang,
    )


@app.post("/voice/synthesize")
def voice_synthesize(payload: Dict[str, Any]) -> Response:
    text = str(payload.get("text") or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="text is required")

    language = str(payload.get("language") or "en").strip().lower()[:2]
    audio_b64 = nitro_synthesize_to_base64(text=text, language=language)
    if not audio_b64:
        return Response(status_code=204)

    try:
        audio_bytes = base64.b64decode(audio_b64)
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to decode audio payload")

    return Response(content=audio_bytes, media_type="audio/wav")


@app.post("/sync/pending")
def sync_pending(payload: Dict[str, Any]) -> Dict[str, Any]:
    pending = payload.get("pending") or []
    if not isinstance(pending, list):
        raise HTTPException(status_code=400, detail="pending must be a list")

    processed = 0
    for item in pending:
        try:
            user_id = str(item.get("user_id") or "").strip()
            message = str(item.get("message") or "").strip()
            if not user_id or not message:
                continue
            detected_lang = str(item.get("detected_language") or "").strip().lower() or detect_language(message)
            bot_id = item.get("bot_id")
            BRAIN.handle_message(
                user_id=user_id,
                message=message,
                persist_chat=True,
                bot_id=str(bot_id) if bot_id else None,
                incoming_language=detected_lang,
            )
            processed += 1
        except Exception:
            continue

    return {"ok": True, "processed": processed}





@app.get("/history/{user_id}", response_model=HistoryResponse)
def history(user_id: str) -> HistoryResponse:
    state = BRAIN.memory.load_user_state(user_id)
    return HistoryResponse(chat_history=state.get("chat_history", []))


@app.get("/languages")
def languages() -> Dict[str, Any]:
    return {"languages": get_supported_languages_list()}


@app.post('/tasks/submit')
def tasks_submit(payload: Dict[str, Any]) -> Dict[str, Any]:
    user_id = str(payload.get('user_id') or '')
    task_type = str(payload.get('task_type') or '')
    task_payload = payload.get('payload') or {}
    if not user_id or not task_type:
        raise HTTPException(status_code=400, detail='user_id and task_type required')
    # Ensure TaskAgent exists
    if not getattr(BRAIN, 'task_agent', None):
        BRAIN.task_agent = BRAIN.task_agent = BRAIN.get_engine('composer') if False else None
    try:
        # If TaskAgent is attached to brain, use its submit_task; otherwise fallback
        if getattr(BRAIN, 'task_agent', None) and hasattr(BRAIN.task_agent, 'submit_task'):
            tid = BRAIN.task_agent.submit_task(task_type, user_id, task_payload)
        else:
            # fallback: use CoreBrain submit_background_task with a noop
            def _noop(uid, payload, progress_callback=None):
                return {"ok": False, "error": "TaskAgent not available"}

            tid = BRAIN.submit_background_task(_noop, user_id, task_payload)
    except Exception:
        raise HTTPException(status_code=500, detail='Failed to submit task')
    return {"ok": True, "task_id": tid}


@app.get('/tasks/{task_id}')
def tasks_get(task_id: str) -> Dict[str, Any]:
    t = BRAIN.get_background_task(task_id)
    if t is None:
        raise HTTPException(status_code=404, detail='task not found')
    return {"ok": True, "task": t}


@app.post("/auth/login", response_model=SaraswatiLoginResponse)
def auth_login(req: SaraswatiLoginRequest) -> SaraswatiLoginResponse:
    external = _validate_saraswati_external(req.account_id, req.password)
    if external:
        user_id = f"saraswati_{external.get('external_id', req.account_id)}"
        display_name = external.get("display_name", req.account_id)
        email = external.get("email", "")
        token = _generate_auth_token({"user_id": user_id, "provider": "saraswati"})
        _save_user_profile(user_id, {"display_name": display_name, "email": email, "provider": "saraswati"})
        return SaraswatiLoginResponse(
            user_id=user_id,
            display_name=display_name,
            email=email,
            token=token,
        )

    validated = _validate_saraswati_account(req.account_id, req.password)
    if not validated:
        raise HTTPException(status_code=401, detail="Invalid Saraswati credentials")

    user_id = f"saraswati_{req.account_id}"
    display_name = validated.get("display_name", req.account_id)
    email = validated.get("email", "")
    token = _generate_auth_token({"user_id": user_id, "provider": "saraswati"})
    _save_user_profile(user_id, {"display_name": display_name, "email": email, "provider": "saraswati"})
    return SaraswatiLoginResponse(
        user_id=user_id,
        display_name=display_name,
        email=email,
        token=token,
    )


@app.post("/auth/saraswati", response_model=SaraswatiLoginResponse)
def saraswati_login(req: SaraswatiLoginRequest) -> SaraswatiLoginResponse:
    return auth_login(req)


@app.get("/auth/verify", response_model=AuthVerifyResponse)
def verify_auth(request: Request, token: str = "") -> AuthVerifyResponse:
    auth_token = token or _get_auth_token_from_request(request)
    if not auth_token:
        raise HTTPException(status_code=401, detail="Authorization token is required")

    payload = _decode_auth_token(auth_token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    user_id = str(payload.get("user_id") or "")
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid auth payload")

    profile = _load_user_profile(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="User profile not found")

    return AuthVerifyResponse(
        user_id=user_id,
        display_name=profile.get("display_name", user_id),
        email=profile.get("email", ""),
        provider=profile.get("provider", "saraswati"),
        token=auth_token,
        valid=True,
    )


@app.get("/bots")
def bots(query: str = "") -> Dict[str, Any]:
    bots_list = BOT_MARKET.list_bots()
    filtered = filter_bots(bots_list, query)
    return {"bots": filtered}


@app.get("/user/preferences/{user_id}")
def get_user_preferences(user_id: str) -> Dict[str, Any]:
    prefs = BRAIN.memory.get_user_preferences(user_id)
    return {"ok": True, "preferences": prefs}


@app.post("/user/preferences")
def set_user_preferences(payload: Dict[str, Any]) -> Dict[str, Any]:
    user_id = str(payload.get("user_id") or "")
    prefs = payload.get("preferences") or {}
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id required")
    BRAIN.memory.set_user_preferences(user_id, prefs)
    return {"ok": True}


@app.get("/bots/{bot_id}/web-policy")
def get_bot_web_policy(bot_id: str, user_id: str = "") -> Dict[str, Any]:
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id required to fetch bot web policy")
    policy = BRAIN.memory.load_bot_web_policy(user_id=user_id, bot_id=bot_id)
    return {"ok": True, "policy": policy}


@app.post("/bots/{bot_id}/web-policy")
def set_bot_web_policy(bot_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    user_id = str(payload.get("user_id") or "")
    policy = payload.get("policy") or {}
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id required to set bot web policy")
    BRAIN.memory.set_bot_web_policy(user_id=user_id, bot_id=bot_id, policy_state=policy)
    return {"ok": True}


@app.get("/bots/{bot_id}/image-policy")
def get_bot_image_policy(bot_id: str, user_id: str = "") -> Dict[str, Any]:
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id required to fetch bot image policy")
    policy = BRAIN.memory.load_bot_image_policy(user_id=user_id, bot_id=bot_id)
    return {"ok": True, "policy": policy}


@app.post("/bots/{bot_id}/image-policy")
def set_bot_image_policy(bot_id: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    user_id = str(payload.get("user_id") or "")
    policy = payload.get("policy") or {}
    if not user_id:
        raise HTTPException(status_code=400, detail="user_id required to set bot image policy")
    BRAIN.memory.set_bot_image_policy(user_id=user_id, bot_id=bot_id, policy_state=policy)
    return {"ok": True}


@app.post('/image/history')
def add_image_history(payload: Dict[str, Any]) -> Dict[str, Any]:
    user_id = str(payload.get('user_id') or '')
    action = payload.get('action') or {}
    if not user_id or not action:
        raise HTTPException(status_code=400, detail='user_id and action required')
    BRAIN.memory.append_image_history(user_id=user_id, image_action=action)
    return {'ok': True}


@app.get('/image/history/{user_id}')
def get_image_history(user_id: str) -> Dict[str, Any]:
    history = BRAIN.memory.get_image_history(user_id)
    return {'ok': True, 'history': history}


@app.post('/image/feedback')
def record_image_feedback(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Record user feedback (like/dislike) for an image. Affects AI globally."""
    image_key = str(payload.get('image_key') or '')
    feedback = str(payload.get('feedback') or '').lower()
    if not image_key or feedback not in ['like', 'dislike']:
        raise HTTPException(status_code=400, detail='image_key and feedback (like/dislike) required')
    BRAIN.memory._record_image_feedback(image_key, feedback)
    stats = BRAIN.memory.get_image_feedback(image_key)
    return {'ok': True, 'stats': stats}


@app.get('/image/feedback/{image_key}')
def get_image_feedback_stats(image_key: str) -> Dict[str, Any]:
    """Get like/dislike stats for an image (used for AI improvement)."""
    stats = BRAIN.memory.get_image_feedback(image_key)
    return {'ok': True, 'stats': stats}


@app.get('/image/feedback-all')
def get_all_feedback() -> Dict[str, Any]:
    """Get all feedback data for AI retraining/analysis."""
    all_fb = BRAIN.memory.get_all_image_feedback()
    return {'ok': True, 'feedback': all_fb}


@app.get("/memory/graph/{user_id}")
def get_memory_graph(user_id: str) -> Dict[str, Any]:
    graph = BRAIN.memory.get_memory_graph(user_id)
    return {"ok": True, "graph": graph}


@app.post("/memory/graph/node")
def add_memory_node(payload: Dict[str, Any]) -> Dict[str, Any]:
    user_id = str(payload.get("user_id") or "")
    node_id = str(payload.get("node_id") or "")
    meta = payload.get("meta") or {}
    if not user_id or not node_id:
        raise HTTPException(status_code=400, detail="user_id and node_id required")
    BRAIN.memory.add_memory_node(user_id, node_id, meta=meta)
    return {"ok": True}


@app.post("/memory/graph/link")
def add_memory_link(payload: Dict[str, Any]) -> Dict[str, Any]:
    user_id = str(payload.get("user_id") or "")
    from_node = str(payload.get("from") or "")
    to_node = str(payload.get("to") or "")
    relation = str(payload.get("relation") or "related")
    if not user_id or not from_node or not to_node:
        raise HTTPException(status_code=400, detail="user_id, from and to required")
    BRAIN.memory.link_memory_nodes(user_id, from_node, to_node, relation=relation)
    return {"ok": True}


@app.get("/memory/recommend/{user_id}")
def recommend_from_memory(user_id: str, seed: str = "") -> Dict[str, Any]:
    if not user_id or not seed:
        raise HTTPException(status_code=400, detail="user_id and seed required")
    recs = BRAIN.memory.recommend_examples_from_graph(user_id, seed)
    return {"ok": True, "recommendations": recs}


@app.post('/tasks/submit')
def submit_task(payload: Dict[str, Any]) -> Dict[str, Any]:
    """Submit a background task. Supported types: 'web_search'."""
    user_id = str(payload.get('user_id') or '')
    task_type = str(payload.get('task_type') or '')
    task_payload = payload.get('payload') or {}
    if not task_type:
        raise HTTPException(status_code=400, detail='task_type required')

    if task_type == 'web_search':
        query = str(task_payload.get('query') or '')
        lang = str(task_payload.get('language') or 'en')
        if not query:
            raise HTTPException(status_code=400, detail='query required for web_search')

        def _task(progress_callback=None):
            # If provided, _handle_live_web_search may call progress_callback intermittently.
            return BRAIN._handle_live_web_search(user_id=user_id or 'guest_task', query=query, language=lang)

        tid = BRAIN.submit_background_task(_task)
        return {'ok': True, 'task_id': tid}

    raise HTTPException(status_code=400, detail='unsupported task_type')


@app.get('/tasks/{task_id}')
def get_task_status(task_id: str) -> Dict[str, Any]:
    t = BRAIN.get_background_task(task_id)
    if t is None:
        raise HTTPException(status_code=404, detail='task not found')
    return {'ok': True, 'task': t}


@app.post("/bots/create-chat")
def bots_create_chat(payload: Dict[str, Any]) -> Dict[str, Any]:
    user_id = str(payload.get("user_id", ""))
    message = str(payload.get("message", ""))
    creator = str(payload.get("creator", "")) or user_id or "Nitro Infinity AI"
    conversation_state = payload.get("state", {}) or {}

    result = create_bot_reply(message, creator=creator, conversation_state=conversation_state)
    return result


@app.post("/bots")
def bots_create_final(payload: Dict[str, Any]) -> Dict[str, Any]:
    creator = str(payload.get("creator", ""))
    state = payload.get("bot", {}) or {}

    bot_id = str(payload.get("bot_id", "")) or f"custom_{creator}_{int(datetime.now(timezone.utc).timestamp())}"

    # Save into marketplace
    from .bots_engine import BotMarketplaceBot

    bot_obj = {
        "name": str(state.get("name", "Custom Bot"))[:40],
        "description": str(state.get("description", ""))[:240] if state.get("description") is not None else "",
        "skills": state.get("skills", []) or [],
        "ratings": float(state.get("ratings", 4.5) or 4.5),
        "creator": str(state.get("creator", "Nitro Infinity AI"))[:60],
        "category": str(state.get("category", "coding"))[:40],
        "icon": str(state.get("icon", "✨"))[:4],

        "educationEnabled": bool(state.get("educationEnabled", False)),
        "professionEnabled": bool(state.get("professionEnabled", False)),
        "professionCategories": list(state.get("professionCategories") or []),
        "workflowAssistanceEnabled": bool(state.get("workflowAssistanceEnabled", False)),
        "webSearchEnabled": bool(state.get("webSearchEnabled", False)),
        "allowedWebCategories": list(state.get("allowedWebCategories") or []),
        "trustedSources": list(state.get("trustedSources") or []),

        "useGlobalLanguageSystem": bool(state.get("useGlobalLanguageSystem", True)),
        "selectedLanguages": list(state.get("selectedLanguages") or state.get("selected_languages") or []),
        "preferredLanguage": state.get("preferredLanguage") or state.get("preferred_language"),
        "voicePreferences": state.get("voicePreferences") or {},
        "imageGenerationEnabled": bool(state.get("imageGenerationEnabled", True)),
        "imageDetectionEnabled": bool(state.get("imageDetectionEnabled", True)),
    }

    BOT_MARKET.add_bot(
        bot_id=bot_id,
        bot=BotMarketplaceBot(
            name=bot_obj["name"],
            description=bot_obj["description"],
            skills=bot_obj["skills"],
            ratings=bot_obj["ratings"],
            creator=bot_obj["creator"],
            category=bot_obj["category"],
            icon=bot_obj["icon"],
            educationEnabled=bot_obj.get("educationEnabled", False),
            professionEnabled=bot_obj.get("professionEnabled", False),
            professionCategories=bot_obj.get("professionCategories") or [],
            workflowAssistanceEnabled=bot_obj.get("workflowAssistanceEnabled", False),
            webSearchEnabled=bot_obj.get("webSearchEnabled", False),
            allowedWebCategories=bot_obj.get("allowedWebCategories") or [],
            trustedSources=bot_obj.get("trustedSources") or [],
            useGlobalLanguageSystem=bot_obj["useGlobalLanguageSystem"],
            selectedLanguages=bot_obj["selectedLanguages"],
            preferredLanguage=str(bot_obj["preferredLanguage"]) if bot_obj.get("preferredLanguage") else None,
            voicePreferences=bot_obj.get("voicePreferences") or {},
            imageGenerationEnabled=bot_obj.get("imageGenerationEnabled", True),
            imageDetectionEnabled=bot_obj.get("imageDetectionEnabled", True),
        ),
    )


    return {"ok": True, "bot_id": bot_id, "bot": bot_obj}



@app.get("/health")
def health() -> Dict[str, Any]:
    return {"ok": True}


@app.get("/metrics")
def metrics() -> Dict[str, Any]:
    try:
        m = BRAIN.get_metrics()
        return {"ok": True, "metrics": m}
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to collect metrics")


@app.get("/metrics/prom")
def metrics_prom(request: Request, api_key: str = "") -> Response:
    """Return a Prometheus-compatible plaintext metrics snapshot. Requires API key if METRICS_API_KEY is set."""
    if not _check_metrics_auth(request, api_key):
        raise HTTPException(status_code=401, detail="Invalid or missing API key for metrics endpoint")
    try:
        m = BRAIN.get_metrics()
        lines = []
        # Cache metrics
        lines.append("# HELP nitro_cache_hits Total cache hits")
        lines.append("# TYPE nitro_cache_hits counter")
        lines.append(f"nitro_cache_hits {int(m.get('cache_hits', 0))}")
        lines.append("# HELP nitro_cache_misses Total cache misses")
        lines.append("# TYPE nitro_cache_misses counter")
        lines.append(f"nitro_cache_misses {int(m.get('cache_misses', 0))}")
        lines.append("# HELP nitro_cache_sets Total cache sets")
        lines.append("# TYPE nitro_cache_sets counter")
        lines.append(f"nitro_cache_sets {int(m.get('cache_sets', 0))}")

        # Engine call counts
        lines.append("# HELP nitro_engine_calls_total Total engine calls per engine")
        lines.append("# TYPE nitro_engine_calls_total counter")
        for en, cnt in (m.get('engine_calls') or {}).items():
            lines.append(f'nitro_engine_calls_total{{engine="{en}"}} {int(cnt)}')

        # Engine latency summary
        lines.append("# HELP nitro_engine_latency_avg_ms Average engine latency in ms")
        lines.append("# TYPE nitro_engine_latency_avg_ms gauge")
        lines.append("# HELP nitro_engine_latency_p95_ms 95th percentile engine latency in ms")
        lines.append("# TYPE nitro_engine_latency_p95_ms gauge")
        for en, stats in (m.get('engine_latency_summary') or {}).items():
            avg = stats.get('avg_ms') or 0
            p95 = stats.get('p95_ms') or 0
            lines.append(f'nitro_engine_latency_avg_ms{{engine="{en}"}} {float(avg)}')
            lines.append(f'nitro_engine_latency_p95_ms{{engine="{en}"}} {float(p95)}')

        payload = "\n".join(lines) + "\n"
        return Response(payload, media_type="text/plain; version=0.0.4; charset=utf-8")
    except Exception:
        raise HTTPException(status_code=500, detail="Failed to collect prom metrics")


# Periodic metrics flusher: write snapshot to disk every N seconds
METRICS_FLUSH_INTERVAL = int(os.environ.get("METRICS_FLUSH_INTERVAL", "30"))
METRICS_FILE = os.path.join(DATA_DIR, "metrics.json")
METRICS_WEBHOOK_URL = os.environ.get("METRICS_WEBHOOK_URL", "")
METRICS_WEBHOOK_SECRET = os.environ.get("METRICS_WEBHOOK_SECRET", "")
METRICS_API_KEY = os.environ.get("METRICS_API_KEY", "")

def _check_metrics_auth(request: Request, api_key_query: str = "") -> bool:
    """Check if request has valid metrics API key (from header or query param)."""
    if not METRICS_API_KEY:
        # No API key configured; allow access
        return True
    # Check Authorization header (Bearer token)
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        if token == METRICS_API_KEY:
            return True
    # Check X-API-Key header
    if request.headers.get("X-API-Key") == METRICS_API_KEY:
        return True
    # Check query param ?api_key=...
    if api_key_query == METRICS_API_KEY:
        return True
    return False

def _metrics_flusher_loop():
    logger = logging.getLogger(__name__)
    while True:
        try:
            snap = BRAIN.get_metrics()
            with open(METRICS_FILE, "w", encoding="utf-8") as f:
                json.dump({"ts": datetime.now(timezone.utc).isoformat(), "metrics": snap}, f, indent=2)
            logger.debug("Flushed metrics to %s", METRICS_FILE)
            # If a webhook URL is configured, POST metrics snapshot with optional HMAC signing
            try:
                url = METRICS_WEBHOOK_URL or os.environ.get("METRICS_WEBHOOK_URL")
                if url:
                    ts = datetime.now(timezone.utc).isoformat()
                    payload_obj = {"ts": ts, "metrics": snap}
                    payload = json.dumps(payload_obj).encode("utf-8")
                    headers = {"Content-Type": "application/json"}
                    secret = (METRICS_WEBHOOK_SECRET or os.environ.get("METRICS_WEBHOOK_SECRET"))
                    try:
                        if secret:
                            sig = hmac.new(secret.encode("utf-8"), payload, hashlib.sha256).hexdigest()
                            headers["X-Metrics-Signature"] = sig
                            headers["X-Metrics-Ts"] = ts
                    except Exception:
                        logger.exception("Failed to compute metrics webhook HMAC signature")

                    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
                    try:
                        with urllib.request.urlopen(req, timeout=8) as resp:
                            logger.debug("Posted metrics to webhook %s, status=%s", url, getattr(resp, 'status', 'n/a'))
                    except Exception as e:
                        logger.warning("Failed to POST metrics to webhook %s: %s", url, str(e))
            except Exception:
                logger.exception("Metrics webhook send failed")
        except Exception:
            try:
                logger.exception("Failed to flush metrics")
            except Exception:
                pass
        try:
            time.sleep(max(5, METRICS_FLUSH_INTERVAL))
        except Exception:
            break


# start flusher thread as daemon
try:
    t = threading.Thread(target=_metrics_flusher_loop, daemon=True)
    t.start()
except Exception:
    logging.getLogger(__name__).exception("Failed to start metrics flusher thread")


def _get_server_settings() -> Dict[str, Any]:
    host = str(os.environ.get("NITRO_HOST", "0.0.0.0")).strip() or "0.0.0.0"
    port = _parse_env_int("NITRO_PORT", 8000)
    workers = _parse_env_int("NITRO_WORKERS", 1)
    log_level = str(os.environ.get("NITRO_LOG_LEVEL", "info")).strip().lower() or "info"
    reload = str(os.environ.get("NITRO_RELOAD", "false")).strip().lower() in ("1", "true", "yes", "on")
    return {
        "host": host,
        "port": port,
        "workers": max(1, workers),
        "log_level": log_level,
        "reload": reload,
        "timeout_keep_alive": 15,
    }


if __name__ == "__main__":
    settings = _get_server_settings()
    logging.getLogger(__name__).info(
        "Starting Nitro Infinity AI backend on %s:%s (workers=%s, data_dir=%s)",
        settings["host"],
        settings["port"],
        settings["workers"],
        DATA_DIR,
    )
    uvicorn.run(
        app,
        host=settings["host"],
        port=settings["port"],
        workers=settings["workers"],
        log_level=settings["log_level"],
        reload=settings["reload"],
        timeout_keep_alive=settings["timeout_keep_alive"],
    )


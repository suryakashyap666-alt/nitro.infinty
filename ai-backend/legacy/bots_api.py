from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from fastapi import APIRouter

from .bots_engine import BotMarketplaceEngine, BotMarketplaceBot
from .bots_logic import create_bot_reply


router = APIRouter(prefix="/bots", tags=["bots"])


@dataclass
class BotListResponse:
    bots: List[Dict[str, Any]]


@dataclass
class CreateBotRequest:
    user_id: str
    message: str
    creator: str
    conversation_state: Dict[str, Any]


@dataclass
class CreateBotResponse:
    reply: str
    done: bool
    botDraft: Dict[str, Any]
    marketplaceBotSaved: Optional[Dict[str, Any]] = None


def _get_engine() -> BotMarketplaceEngine:
    # storage_path is resolved relative to backend package by BotMarketplaceEngine itself.
    # backend/main.py already uses CoreBrain storage_path; here we piggy-back on the same json file.
    # BotMarketplaceEngine expects a storage path passed in, so we will instantiate in endpoints.
    raise RuntimeError("Bot engine must be initialized in endpoints")


@router.get("", response_model=Dict[str, Any])
def list_bots() -> Dict[str, Any]:
    # Create engine with same storage file Nitro already uses.
    # backend/main.py loads DATA_DIR = <backend>/data and CoreBrain uses <DATA_DIR>/nitro_state.json
    import os
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)
    storage_path = os.path.join(data_dir, "nitro_state.json")

    engine = BotMarketplaceEngine(storage_path=storage_path)
    engine.ensure_default_bots()
    return {"bots": engine.list_bots()}


@router.post("/create", response_model=Dict[str, Any])
def create_bot(req: Dict[str, Any]) -> Dict[str, Any]:
    import os
    data_dir = os.path.join(os.path.dirname(__file__), "data")
    os.makedirs(data_dir, exist_ok=True)
    storage_path = os.path.join(data_dir, "nitro_state.json")

    engine = BotMarketplaceEngine(storage_path=storage_path)
    engine.ensure_default_bots()

    user_id = str(req.get("user_id") or "")
    message = str(req.get("message") or "")
    creator = str(req.get("creator") or "Nitro Infinity AI")
    conversation_state = req.get("conversation_state") or {}

    result = create_bot_reply(user_text=message, creator=creator, conversation_state=conversation_state)

    out: Dict[str, Any] = {
        "reply": result.get("reply", ""),
        "done": bool(result.get("done")),
        "botDraft": result.get("botDraft") or {},
    }

    if out["done"]:
        # Save to marketplace and include saved bot.
        botDraft = out["botDraft"]
        bot_id = (
            f"custom_{user_id}_{botDraft.get('name','').replace(' ','_')}_{hash(str(botDraft))}"[:220]
            if user_id
            else f"custom_{hash(str(botDraft))}"
        )

        # Bot multilingual language system settings
        use_global_lang = bool(botDraft.get("useGlobalLanguageSystem", True))
        selected_langs = botDraft.get("selectedLanguages") or botDraft.get("selected_languages") or []
        preferred_lang = botDraft.get("preferredLanguage") or botDraft.get("preferred_language")

        bot = BotMarketplaceBot(
            name=str(botDraft.get("name", "Custom Bot")),
            description=str(botDraft.get("description", "")),
            skills=list(botDraft.get("skills") or []),
            ratings=float(botDraft.get("ratings") or 4.5),
            creator=str(botDraft.get("creator") or creator or "Nitro Infinity AI"),
            category=str(botDraft.get("category") or "coding"),
            icon=str(botDraft.get("icon") or "✨"),
            educationEnabled=bool(botDraft.get("educationEnabled", False)),
            professionEnabled=bool(botDraft.get("professionEnabled", False)),
            professionCategories=list(botDraft.get("professionCategories") or []),
            workflowAssistanceEnabled=bool(botDraft.get("workflowAssistanceEnabled", False)),
            webSearchEnabled=bool(botDraft.get("webSearchEnabled", False)),
            allowedWebCategories=list(botDraft.get("allowedWebCategories") or []),
            trustedSources=list(botDraft.get("trustedSources") or []),
            useGlobalLanguageSystem=use_global_lang,
            selectedLanguages=list(selected_langs or []),
            preferredLanguage=str(preferred_lang) if preferred_lang else None,
            # context intelligence flags (creator may enable these)
            contextUnderstandingEnabled=bool(botDraft.get("contextUnderstandingEnabled", False)),
            userHistoryUnderstandingEnabled=bool(botDraft.get("userHistoryUnderstandingEnabled", False)),
            webAssistanceEnabled=bool(botDraft.get("webAssistanceEnabled", False)),
        )


        engine.add_bot(bot_id=bot_id, bot=bot)
        out["marketplaceBotSaved"] = bot.to_dict()

    return out


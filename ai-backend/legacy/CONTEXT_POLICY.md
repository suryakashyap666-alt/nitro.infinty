# Context Policies & Guest-mode Rules (Nitro Infinity AI)

Summary
-------
This document describes the lightweight Context Understanding / Conversation Intelligence policies added to Nitro Infinity AI, how they behave for MAIN vs bots vs guest users, and where to configure them (API + UI).

Behavior Overview
-----------------
- MAIN Nitro Infinity AI: Context understanding is ON by default and may use saved user history and preferences to resolve references and improve intent detection.
- Bots: Context features are OFF by default. Bot creators can opt a bot into context understanding, user-history usage, and web assistance. These controls are per-creator and stored in user-scoped state.
- Guest Mode: Users whose id begins with `guest_` are treated as guests. Guest-mode prohibits saving long-term memory and disallows reading persisted user history for context. Context analysis may still use the current session messages only.

Context Sources
---------------
The context engine may consider (when allowed by policy):
- Current message
- Recent messages in the active chat session
- Persisted chat history (only for non-guest users and when bot/user policy allows)
- User preferences and interests (persisted profile)

Intent Detection & Clarification
--------------------------------
- The ContextEngine performs simple intent/topic detection and lightweight pronoun/reference resolution.
- If confidence is low, Nitro will ask a clarification question rather than guessing (example: "I see two possible meanings. Did you mean A or B?").

Smart Response & Web Assistance
-------------------------------
- When enabled, bots may be allowed to perform live web searches for time-sensitive queries and summarize trusted sources.
- Web assistance is gated per-bot; creators can enable/disable it and define allowed categories/trusted sources.

Configuration & Persistence
--------------------------
- Per-bot policies are stored in the workspace state file (nitro_state.json) via `MemoryEngine` under user-scoped keys (see `load_bot_context_policy` / `set_bot_context_policy`).
- Backend REST endpoints:
  - `GET /bots/{bot_id}/context-policy` — returns current policy for the authenticated creator
  - `POST /bots/{bot_id}/context-policy` — set/update policy for the bot

UI Integration
--------------
- Bot creation UI (`frontend/src/components/BotCreateScreen.js`) exposes toggles for:
  - Context understanding (on/off)
  - Use user history for context (on/off)
  - Enable web assistance (on/off)
- These settings are sent to the backend during bot creation and can be edited using the REST endpoints above (post-creation settings page can call the same endpoints).

Safety & Privacy Notes
----------------------
- Guest users never have long-term memory written to disk; their chats remain session-scoped.
- Bot policies are creator-scoped; a bot only uses persisted user history for context when the creator has explicitly allowed it and the interacting user is not a guest.
- The ContextEngine is intentionally rule-based and lightweight to avoid heavy ML dependencies; it can be upgraded later for more robust coreference and intent models.

Where To Look In Code
---------------------
- Context engine: `backend/brain/context_engine.py`
- Core integration: `backend/brain/core.py` (look for `context` engine usage in `handle_message`)
- Memory helpers: `backend/brain/memory.py` (`load_bot_context_policy`, `set_bot_context_policy`)
- Frontend toggles: `frontend/src/components/BotCreateScreen.js`
- Message UI (concise-first + Show More): `frontend/src/components/Message.js` and `frontend/src/styles.css`

If you'd like, I can add a brief API doc with example `curl` calls or add a small settings page in the frontend to edit a bot's context policy post-creation.

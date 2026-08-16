import tempfile
from backend.brain.memory import MemoryEngine


def test_bot_context_policy_set_and_get(tmp_path):
    storage = str(tmp_path / "state.json")
    me = MemoryEngine(storage_path=storage)
    user = "user_abc"
    bot = "bot_1"

    policy = {
        "contextUnderstandingEnabled": True,
        "useUserHistoryUnderstanding": True,
        "useWebAssistance": False,
    }

    me.set_bot_context_policy(user, bot, policy)
    loaded = me.load_bot_context_policy(user, bot)
    assert isinstance(loaded, dict)
    assert loaded.get("contextUnderstandingEnabled") is True


def test_guest_cannot_set_bot_policy(tmp_path):
    storage = str(tmp_path / "state.json")
    me = MemoryEngine(storage_path=storage)
    user = "guest_42"
    bot = "bot_guest"

    policy = {"contextUnderstandingEnabled": True}
    me.set_bot_context_policy(user, bot, policy)
    loaded = me.load_bot_context_policy(user, bot)
    # guests should get default (False)
    assert loaded.get("contextUnderstandingEnabled") is False

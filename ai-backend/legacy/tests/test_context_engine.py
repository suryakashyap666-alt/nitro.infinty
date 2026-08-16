import tempfile
import os

from backend.brain.context_engine import ContextEngine
from backend.brain.memory import MemoryEngine


def test_context_resolve_and_clarify(tmp_path):
    storage = str(tmp_path / "state.json")
    # ensure file created
    me = MemoryEngine(storage_path=storage)
    user_id = "user_123"

    # seed history mentioning a laptop
    me.append_message(user_id, "I'm looking at a gaming laptop called PredatorX", "ok", emotion="neutral", topic="hardware")

    ce = ContextEngine(storage_path=storage)

    analysis = ce.analyze_message(user_id=user_id, message="How much RAM does it need?")

    # Either resolved references should be present (best-effort) or a clarification should be suggested
    assert isinstance(analysis, dict)
    assert "resolved_message" in analysis
    assert (analysis.get("resolved_references") or analysis.get("clarification"))


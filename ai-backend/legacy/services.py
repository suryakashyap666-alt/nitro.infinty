from __future__ import annotations

from typing import Any, Dict, List, Optional
from brain.core import CoreBrain


class NitroServiceCoordinator:
    """Service coordinator for Nitro Infinity AI integrations."""

    def __init__(self, brain: CoreBrain) -> None:
        self.brain = brain
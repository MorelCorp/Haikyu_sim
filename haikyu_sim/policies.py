"""Decision policies for the volleyball card game simulator."""
from __future__ import annotations

from typing import List, Optional


class Constraint:
    HIGH = "HIGH"
    LOW = "LOW"


class BasicPolicy:
    """Simple deterministic policy used for the first-pass simulator."""

    def choose_serve(self, hand: List[int]) -> Optional[int]:
        return self._choose_minimal(hand)

    def choose_block(self, hand: List[int], target: int, window: int) -> Optional[int]:
        lower = max(1, target - window)
        upper = min(13, target + window)
        candidates = [card for card in hand if lower <= card <= upper]
        if not candidates:
            return None
        return min(candidates)

    def choose_card(self, hand: List[int], constraint: str, target: int) -> Optional[int]:
        if constraint == Constraint.HIGH:
            candidates = [card for card in hand if card > target]
        else:
            candidates = [card for card in hand if card < target]
        if not candidates:
            return None
        return min(candidates)

    def _choose_minimal(self, hand: List[int]) -> Optional[int]:
        return min(hand, default=None)

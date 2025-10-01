"""Deck management for the volleyball card game simulator."""
from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List


@dataclass
class Deck:
    include_specials: bool = False
    rng: random.Random = field(default_factory=random.Random)

    def __post_init__(self) -> None:
        self._draw_pile: List[int] = []
        self._discard_pile: List[int] = []
        self.reshuffles: int = 0
        self._build()

    def _build(self) -> None:
        cards: List[int] = []
        for _ in range(4):
            cards.extend(range(1, 14))
        if self.include_specials:
            cards.extend(range(1, 14))
        self._draw_pile = cards
        self.shuffle()

    def shuffle(self) -> None:
        self.rng.shuffle(self._draw_pile)

    def draw(self) -> int:
        if not self._draw_pile:
            self._reshuffle_discard()
        if not self._draw_pile:
            raise RuntimeError("Deck is exhausted and cannot be reshuffled")
        return self._draw_pile.pop()

    def discard(self, card: int) -> None:
        self._discard_pile.append(card)

    def _reshuffle_discard(self) -> None:
        if not self._discard_pile:
            return
        self._draw_pile = self._discard_pile
        self._discard_pile = []
        self.shuffle()
        self.reshuffles += 1

    def remaining(self) -> int:
        return len(self._draw_pile)

    def discard_count(self) -> int:
        return len(self._discard_pile)

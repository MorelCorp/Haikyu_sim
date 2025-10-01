"""Configuration objects for the Haikyu simulator."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class SimulatorConfig:
    """Runtime configuration for the volleyball card game simulator."""

    num_games: int = 10
    points_to_win: int = 25
    hand_size_per_player: int = 5
    players_per_team: int = 3
    include_specials: bool = False
    block_window: int = 0
    two_touch_penalty: int = 2
    two_touch_penalty_enabled: bool = True
    rally_cap: int = 40
    seed: Optional[int] = None
    log_rallies: bool = True

    def team_hand_size(self) -> int:
        return self.hand_size_per_player * self.players_per_team

    def __post_init__(self) -> None:
        if self.num_games <= 0:
            raise ValueError("num_games must be positive")
        if self.points_to_win <= 0:
            raise ValueError("points_to_win must be positive")
        if self.hand_size_per_player <= 0:
            raise ValueError("hand_size_per_player must be positive")
        if self.players_per_team <= 0:
            raise ValueError("players_per_team must be positive")
        if self.block_window < 0:
            raise ValueError("block_window cannot be negative")
        if self.two_touch_penalty < 0:
            raise ValueError("two_touch_penalty cannot be negative")
        if self.rally_cap <= 0:
            raise ValueError("rally_cap must be positive")

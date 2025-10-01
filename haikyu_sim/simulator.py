"""Core simulator for the Volleyball Card Game."""
from __future__ import annotations

import random
import statistics
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from .config import SimulatorConfig
from .deck import Deck
from .policies import BasicPolicy, Constraint

STEP_LABELS = ["RECV", "PASS", "ATK"]


@dataclass
class TeamState:
    name: str
    policy: BasicPolicy
    hand: List[int] = field(default_factory=list)

    def remove_card(self, card: int) -> None:
        self.hand.remove(card)

    def add_card(self, card: int) -> None:
        self.hand.append(card)

    def hand_size(self) -> int:
        return len(self.hand)


@dataclass
class SequenceOutcome:
    success: bool
    attack_value: Optional[int]
    cards_played: int
    end_reason: Optional[str] = None
    two_touch_used: bool = False
    two_touch_step: Optional[str] = None
    block_attempted: bool = False
    block_success: bool = False


@dataclass
class RallyLog:
    rally_id: int
    server: str
    cards_played: int
    winner: str
    end_reason: str
    block_attempted: bool
    block_success: bool
    two_touch_used_by: Optional[str]
    two_touch_step: Optional[str]
    two_touch_success: Optional[bool]
    start_hand_sizes: Dict[str, int]
    end_hand_sizes: Dict[str, int]
    reshuffles: int


@dataclass
class SimulationReport:
    config: SimulatorConfig
    rally_logs: List[RallyLog]
    aggregate: Dict[str, float]


class GameSimulator:
    """Runs full games consisting of a series of rallies."""

    def __init__(self, config: SimulatorConfig) -> None:
        self.config = config
        self.rng = random.Random(config.seed)
        self.policy = BasicPolicy()

    def run(self) -> SimulationReport:
        rally_logs: List[RallyLog] = []
        rally_lengths: List[int] = []
        server_points = 0
        total_points = 0
        sideout_points = 0
        block_attempts = 0
        block_successes = 0
        two_touch_usage = 0
        two_touch_wins = 0
        exhaustion_ends = 0

        for _ in range(self.config.num_games):
            game_logs, stats = self._play_game()
            rally_logs.extend(game_logs)
            rally_lengths.extend(stats["rally_lengths"])
            server_points += stats["server_points"]
            total_points += stats["total_points"]
            sideout_points += stats["sideout_points"]
            block_attempts += stats["block_attempts"]
            block_successes += stats["block_successes"]
            two_touch_usage += stats["two_touch_usage"]
            two_touch_wins += stats["two_touch_wins"]
            exhaustion_ends += stats["exhaustion_ends"]

        aggregate: Dict[str, float] = {}
        if rally_lengths:
            aggregate["average_rally_length"] = sum(rally_lengths) / len(rally_lengths)
            aggregate["median_rally_length"] = statistics.median(rally_lengths)
        aggregate["server_win_rate"] = server_points / total_points if total_points else 0.0
        aggregate["sideout_rate"] = sideout_points / total_points if total_points else 0.0
        aggregate["block_attempt_rate"] = block_attempts / len(rally_lengths) if rally_lengths else 0.0
        aggregate["block_success_rate"] = (
            block_successes / block_attempts if block_attempts else 0.0
        )
        aggregate["two_touch_usage_rate"] = (
            two_touch_usage / len(rally_lengths) if rally_lengths else 0.0
        )
        aggregate["two_touch_win_rate"] = (
            two_touch_wins / two_touch_usage if two_touch_usage else 0.0
        )
        aggregate["exhaustion_end_rate"] = (
            exhaustion_ends / len(rally_lengths) if rally_lengths else 0.0
        )

        return SimulationReport(config=self.config, rally_logs=rally_logs, aggregate=aggregate)

    def _play_game(self) -> Tuple[List[RallyLog], Dict[str, List[int] | int]]:
        deck = Deck(include_specials=self.config.include_specials, rng=self.rng)
        teams = [
            TeamState(name="A", policy=self.policy),
            TeamState(name="B", policy=self.policy),
        ]
        for team in teams:
            self._draw_up(team, deck)

        scores = [0, 0]
        server_index = 0
        rally_id = 0
        rally_logs: List[RallyLog] = []
        rally_lengths: List[int] = []
        server_points = 0
        sideout_points = 0
        block_attempts = 0
        block_successes = 0
        two_touch_usage = 0
        two_touch_wins = 0
        exhaustion_ends = 0
        while max(scores) < self.config.points_to_win:
            rally_id += 1
            rally = Rally(
                config=self.config,
                deck=deck,
                teams=teams,
                server_index=server_index,
                rng=self.rng,
            )
            outcome = rally.play(rally_id)
            rally_logs.append(outcome.log)
            rally_lengths.append(outcome.log.cards_played)
            block_attempts += outcome.block_attempts
            block_successes += outcome.block_successes
            if outcome.two_touch_used:
                two_touch_usage += 1
                if outcome.log.winner == outcome.two_touch_used:
                    two_touch_wins += 1
            if outcome.log.end_reason in {"NO_RECV", "NO_PASS", "NO_ATTACK"}:
                exhaustion_ends += 1
            winner_index = 0 if outcome.log.winner == "A" else 1
            scores[winner_index] += 1
            if winner_index == server_index:
                server_points += 1
            else:
                sideout_points += 1
                server_index = winner_index
            self._draw_up(teams[0], deck)
            self._draw_up(teams[1], deck)
        total_points = sum(scores)
        stats: Dict[str, List[int] | int] = {
            "rally_lengths": rally_lengths,
            "server_points": server_points,
            "total_points": total_points,
            "sideout_points": sideout_points,
            "block_attempts": block_attempts,
            "block_successes": block_successes,
            "two_touch_usage": two_touch_usage,
            "two_touch_wins": two_touch_wins,
            "exhaustion_ends": exhaustion_ends,
        }
        return rally_logs, stats

    def _draw_up(self, team: TeamState, deck: Deck) -> None:
        target_size = self.config.team_hand_size()
        while team.hand_size() < target_size:
            card = deck.draw()
            team.add_card(card)


@dataclass
class RallyOutcome:
    log: RallyLog
    block_attempts: int
    block_successes: int
    two_touch_used: Optional[str]


class Rally:
    def __init__(
        self,
        config: SimulatorConfig,
        deck: Deck,
        teams: List[TeamState],
        server_index: int,
        rng: random.Random,
    ) -> None:
        self.config = config
        self.deck = deck
        self.teams = teams
        self.server_index = server_index
        self.rng = rng

    def play(self, rally_id: int) -> RallyOutcome:
        active_index = self.server_index
        inactive_index = 1 - self.server_index
        active = self.teams[active_index]
        inactive = self.teams[inactive_index]
        start_sizes = {team.name: team.hand_size() for team in self.teams}

        serve_card = active.policy.choose_serve(active.hand)
        if serve_card is None:
            raise RuntimeError("Server has no card to play")
        active.remove_card(serve_card)
        self.deck.discard(serve_card)
        cards_played = 1
        last_attack = serve_card
        two_touch_used_by: Optional[str] = None
        two_touch_step: Optional[str] = None
        two_touch_pending = {0: 0, 1: 0}
        block_attempts = 0
        block_successes = 0

        last_play_was_attack = False

        while True:
            if cards_played >= self.config.rally_cap:
                winner = inactive.name
                end_reason = "CAP_RALLY_LIMIT"
                break
            inactive_outcome = self._sequence_turn(
                team_index=inactive_index,
                constraints=[Constraint.HIGH, Constraint.LOW, Constraint.LOW],
                incoming_value=last_attack,
                pending_bonus=two_touch_pending[inactive_index],
                allow_block=last_play_was_attack,
            )
            block_attempts += int(inactive_outcome.block_attempted)
            block_successes += int(inactive_outcome.block_success)
            two_touch_pending[inactive_index] = 0
            cards_played += inactive_outcome.cards_played
            if not inactive_outcome.success:
                winner = active.name
                end_reason = inactive_outcome.end_reason or "UNKNOWN"
                break
            if inactive_outcome.two_touch_used and two_touch_used_by is None:
                two_touch_used_by = inactive.name
                two_touch_step = inactive_outcome.two_touch_step
                if self.config.two_touch_penalty_enabled:
                    two_touch_pending[active_index] = self.config.two_touch_penalty
            last_attack = inactive_outcome.attack_value if inactive_outcome.attack_value is not None else last_attack
            last_play_was_attack = inactive_outcome.attack_value is not None
            if cards_played >= self.config.rally_cap:
                winner = active.name
                end_reason = "CAP_RALLY_LIMIT"
                break
            active_outcome = self._sequence_turn(
                team_index=active_index,
                constraints=[Constraint.LOW, Constraint.HIGH, Constraint.HIGH],
                incoming_value=last_attack,
                pending_bonus=two_touch_pending[active_index],
                allow_block=last_play_was_attack,
            )
            block_attempts += int(active_outcome.block_attempted)
            block_successes += int(active_outcome.block_success)
            two_touch_pending[active_index] = 0
            cards_played += active_outcome.cards_played
            if not active_outcome.success:
                winner = inactive.name
                end_reason = active_outcome.end_reason or "UNKNOWN"
                break
            if active_outcome.two_touch_used and two_touch_used_by is None:
                two_touch_used_by = active.name
                two_touch_step = active_outcome.two_touch_step
                if self.config.two_touch_penalty_enabled:
                    two_touch_pending[inactive_index] = self.config.two_touch_penalty
            last_attack = active_outcome.attack_value if active_outcome.attack_value is not None else last_attack
            last_play_was_attack = active_outcome.attack_value is not None

        end_sizes = {team.name: team.hand_size() for team in self.teams}
        log = RallyLog(
            rally_id=rally_id,
            server=active.name,
            cards_played=cards_played,
            winner=winner,
            end_reason=end_reason,
            block_attempted=block_attempts > 0,
            block_success=block_successes > 0,
            two_touch_used_by=two_touch_used_by,
            two_touch_step=two_touch_step,
            two_touch_success=(winner == two_touch_used_by) if two_touch_used_by else None,
            start_hand_sizes=start_sizes,
            end_hand_sizes=end_sizes,
            reshuffles=self.deck.reshuffles,
        )
        return RallyOutcome(
            log=log,
            block_attempts=block_attempts,
            block_successes=block_successes,
            two_touch_used=two_touch_used_by,
        )

    def _sequence_turn(
        self,
        team_index: int,
        constraints: List[str],
        incoming_value: int,
        pending_bonus: int,
        allow_block: bool,
    ) -> SequenceOutcome:
        team = self.teams[team_index]
        last_value = incoming_value
        cards_played = 0
        pending_applied = False

        # Block check occurs before reception
        block_card: Optional[int] = None
        if allow_block:
            block_window = self.config.block_window
            if block_window >= 0:
                block_card = team.policy.choose_block(team.hand, incoming_value, block_window)
        if block_card is not None:
            return SequenceOutcome(
                success=True,
                attack_value=incoming_value,
                cards_played=0,
                two_touch_used=False,
                block_attempted=True,
                block_success=True,
            )

        for index, constraint in enumerate(constraints):
            step_label = STEP_LABELS[index]
            target = last_value
            bonus = 0
            if index == 0 and pending_bonus and not pending_applied:
                bonus = pending_bonus
                pending_applied = True
            adjusted_target = self._adjust_target(constraint, target, bonus)
            card = self._choose_card(team, constraint, adjusted_target)
            if card is None:
                reason = {
                    "RECV": "NO_RECV",
                    "PASS": "NO_PASS",
                    "ATK": "NO_ATTACK",
                }[step_label]
                return SequenceOutcome(
                    success=False,
                    attack_value=None,
                    cards_played=cards_played,
                    end_reason=reason,
                )
            team.remove_card(card)
            self.deck.discard(card)
            cards_played += 1
            last_value = card
            if step_label != "ATK":
                if self._should_two_touch(team.hand, constraints, index, last_value):
                    return SequenceOutcome(
                        success=True,
                        attack_value=last_value,
                        cards_played=cards_played,
                        two_touch_used=True,
                        two_touch_step=step_label,
                    )
            else:
                return SequenceOutcome(
                    success=True,
                    attack_value=last_value,
                    cards_played=cards_played,
                )
        return SequenceOutcome(success=True, attack_value=last_value, cards_played=cards_played)

    def _choose_card(self, team: TeamState, constraint: str, target: int) -> Optional[int]:
        card = team.policy.choose_card(team.hand, constraint, target)
        return card

    def _should_two_touch(self, hand: List[int], constraints: List[str], index: int, last_value: int) -> bool:
        if index >= len(constraints) - 1:
            return False
        next_constraint = constraints[index + 1]
        target = last_value
        if next_constraint == Constraint.HIGH:
            return not any(card > target for card in hand)
        return not any(card < target for card in hand)

    def _adjust_target(self, constraint: str, target: int, bonus: int) -> int:
        if bonus <= 0:
            return target
        if constraint == Constraint.HIGH:
            return max(0, target - bonus)
        return min(13, target + bonus)

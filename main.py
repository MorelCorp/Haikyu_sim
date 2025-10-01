"""Entry point for running the Haikyu volleyball card game simulator."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from haikyu_sim import GameSimulator, SimulatorConfig


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the Haikyu volleyball card game simulator")
    parser.add_argument("--config", type=Path, help="Path to JSON config file", default=None)
    parser.add_argument("--games", type=int, default=None, help="Override number of games to simulate")
    parser.add_argument("--seed", type=int, default=None, help="Random seed override")
    parser.add_argument("--points", type=int, default=None, help="Points required to win a game")
    return parser.parse_args()


def load_config(path: Path | None) -> SimulatorConfig:
    if path is None:
        return SimulatorConfig()
    data = json.loads(path.read_text())
    return SimulatorConfig(**data)


def main() -> None:
    args = parse_args()
    config = load_config(args.config)
    if args.games is not None:
        config.num_games = args.games
    if args.seed is not None:
        config.seed = args.seed
    if args.points is not None:
        config.points_to_win = args.points
    simulator = GameSimulator(config)
    report = simulator.run()
    print("=== Aggregate Metrics ===")
    for key, value in sorted(report.aggregate.items()):
        print(f"{key}: {value:.3f}")
    if config.log_rallies:
        print("\n=== Sample Rally Logs ===")
        for log in report.rally_logs[:10]:
            print(
                f"Rally {log.rally_id} | Server {log.server} | Winner {log.winner} | "
                f"Cards {log.cards_played} | End {log.end_reason}"
            )


if __name__ == "__main__":
    main()

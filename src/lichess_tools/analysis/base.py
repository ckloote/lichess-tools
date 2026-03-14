from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class EvalResult:
    ply: int
    move_san: str
    eval_cp: int | None  # centipawns (None if mate)
    mate_in: int | None  # non-None when eval is a mate score
    color: str  # "white" or "black" (who moved)

    @property
    def numeric_cp(self) -> int:
        """Return a numeric centipawn value for comparison. Mate scores use ±30000."""
        if self.mate_in is not None:
            return 30000 if self.mate_in > 0 else -30000
        return self.eval_cp or 0


@dataclass
class CriticalMoment:
    game_id: str
    ply: int
    move_san: str
    eval_before_cp: int
    eval_after_cp: int
    swing_cp: int
    color: str  # player who made the blunder
    engine: str  # "cloud" or "stockfish"


class AnalysisEngine(ABC):
    @abstractmethod
    def evaluate_position(self, fen: str) -> EvalResult | None:
        """Evaluate a single position. Returns None if unavailable."""

    @abstractmethod
    def analyze_game(self, pgn_text: str) -> list[EvalResult]:
        """Return per-move eval list for the given PGN."""

    def find_critical_moments(
        self,
        game_id: str,
        evals: list[EvalResult],
        threshold_cp: int,
    ) -> list[CriticalMoment]:
        """Find moves where the eval swing exceeds threshold_cp."""
        moments: list[CriticalMoment] = []
        for i in range(1, len(evals)):
            prev = evals[i - 1]
            curr = evals[i]
            # Swing from the perspective of the side to move
            swing = abs(curr.numeric_cp - prev.numeric_cp)
            if swing >= threshold_cp:
                moments.append(
                    CriticalMoment(
                        game_id=game_id,
                        ply=curr.ply,
                        move_san=curr.move_san,
                        eval_before_cp=prev.numeric_cp,
                        eval_after_cp=curr.numeric_cp,
                        swing_cp=swing,
                        color=curr.color,
                        engine=self.engine_name,
                    )
                )
        return moments

    @property
    @abstractmethod
    def engine_name(self) -> str:
        """Short name for this engine (e.g. 'cloud', 'stockfish')."""

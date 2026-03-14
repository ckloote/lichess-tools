from __future__ import annotations

import io

import chess
import chess.pgn

from lichess_tools.analysis.base import AnalysisEngine, EvalResult
from lichess_tools.analysis.pgn import extract_evals_from_pgn


class CloudEngine(AnalysisEngine):
    """
    Analysis engine that uses Lichess cloud evaluations.

    Primary path: parse [%eval] annotations already embedded in the PGN.
    Fallback path: query /api/cloud-eval for positions without annotations.
    """

    def __init__(self, client=None, *, fallback_to_api: bool = True):
        """
        Args:
            client: LichessClient instance (needed only for fallback API calls).
            fallback_to_api: If True, query cloud-eval API for unannotated positions.
        """
        self._client = client
        self._fallback_to_api = fallback_to_api

    @property
    def engine_name(self) -> str:
        return "cloud"

    def evaluate_position(self, fen: str) -> EvalResult | None:
        """Query Lichess cloud-eval endpoint for a single FEN."""
        if self._client is None:
            return None
        try:
            data = self._client.get_json("/api/cloud-eval", params={"fen": fen, "multiPv": 1})
            pvs = data.get("pvs", [])
            if not pvs:
                return None
            pv = pvs[0]
            cp = pv.get("cp")
            mate = pv.get("mate")
            return EvalResult(
                ply=0,
                move_san="",
                eval_cp=cp,
                mate_in=mate,
                color="white",
            )
        except Exception:
            return None

    def analyze_game(self, pgn_text: str) -> list[EvalResult]:
        """
        Extract evals from embedded PGN annotations.
        Falls back to /api/cloud-eval for moves without annotations if enabled.
        """
        evals = extract_evals_from_pgn(pgn_text)

        if evals:
            return evals

        if not self._fallback_to_api or self._client is None:
            return []

        return self._analyze_via_api(pgn_text)

    def _analyze_via_api(self, pgn_text: str) -> list[EvalResult]:
        """Walk each position and query cloud-eval for its evaluation."""
        game = chess.pgn.read_game(io.StringIO(pgn_text))
        if game is None:
            return []

        results: list[EvalResult] = []
        node = game
        ply = 0

        while node.variations:
            next_node = node.variation(0)
            move = next_node.move
            ply += 1

            board = node.board()
            color = "white" if board.turn == chess.WHITE else "black"
            san = board.san(move)

            board.push(move)
            fen = board.fen()

            result = self.evaluate_position(fen)
            if result is not None:
                results.append(
                    EvalResult(
                        ply=ply,
                        move_san=san,
                        eval_cp=result.eval_cp,
                        mate_in=result.mate_in,
                        color=color,
                    )
                )

            node = next_node

        return results

from __future__ import annotations

import io
import re

import chess
import chess.pgn

from lichess_tools.analysis.base import EvalResult

_EVAL_RE = re.compile(r"\[%eval\s+([^\]]+)\]")
_MATE_RE = re.compile(r"#(-?\d+)")
_CP_RE = re.compile(r"^(-?\d+(?:\.\d+)?)$")


def _parse_eval_comment(comment: str) -> tuple[int | None, int | None]:
    """
    Parse a [%eval ...] comment.
    Returns (eval_cp, mate_in). eval_cp is centipawns * 100 (stored as int).
    If it's a mate score like '#3', returns (None, 3).
    """
    m = _EVAL_RE.search(comment)
    if not m:
        return None, None
    raw = m.group(1).strip()
    mate_m = _MATE_RE.match(raw)
    if mate_m:
        return None, int(mate_m.group(1))
    cp_m = _CP_RE.match(raw)
    if cp_m:
        # Lichess stores evals in pawns (e.g. 0.25), convert to centipawns
        return int(float(cp_m.group(1)) * 100), None
    return None, None


def extract_evals_from_pgn(pgn_text: str) -> list[EvalResult]:
    """
    Parse a PGN string and extract per-move eval annotations.
    Returns a list of EvalResult in ply order (ply 1 = white's first move).
    Only includes moves that have an [%eval] comment.
    """
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

        # The comment after a move is on the *next* node
        comment = next_node.comment or ""
        eval_cp, mate_in = _parse_eval_comment(comment)

        if eval_cp is not None or mate_in is not None:
            board = node.board()
            color = "white" if board.turn == chess.WHITE else "black"
            san = board.san(move)
            results.append(
                EvalResult(
                    ply=ply,
                    move_san=san,
                    eval_cp=eval_cp,
                    mate_in=mate_in,
                    color=color,
                )
            )

        node = next_node

    return results


def parse_game_headers(pgn_text: str) -> dict:
    """Extract PGN headers as a dict."""
    game = chess.pgn.read_game(io.StringIO(pgn_text))
    if game is None:
        return {}
    return dict(game.headers)

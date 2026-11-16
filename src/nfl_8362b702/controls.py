"""Control baselines: deterministic random picks and rating-favorites.

Both controls run over exactly the same games as any strategy they police.
The random control's seed and draw rule are pre-registered; the output is
reproducible bit for bit. Neither control ever sees a price.
"""
from __future__ import annotations

import hashlib

from .model import ratings, MODEL_ID
from .results import corpus_rows

RANDOM_SEED_HEX = hashlib.sha256(b"nfl_8362b702/controls/v1").hexdigest()[:8]
RANDOM_SEED = int(RANDOM_SEED_HEX, 16)


def random_pick(game_id: str) -> str:
    """Deterministic pre-registered draw: parity of sha256(seed|game_id)."""
    h = hashlib.sha256(f"{RANDOM_SEED_HEX}|{game_id}".encode()).hexdigest()
    bit = int(h[:8], 16) & 1
    return "home" if bit else "away"


def favorite_pick(game_id, away, home, rat):
    """Rating favorite: higher corpus strength; tie-break higher PF/g."""
    sa, sh = rat[away], rat[home]
    if sh["strength"] != sa["strength"]:
        return "home" if sh["strength"] > sa["strength"] else "away"
    return "home" if sh["off_ppg"] > sa["off_ppg"] else "away"


def control_rows(games):
    """One row per game per control, with the pick and the frozen draw."""
    rat = ratings(corpus_rows())
    out = []
    for g in games:
        out.append({"control_id": "S8362-RANDOM", "game_id": g["game_id"],
                    "pick": random_pick(g["game_id"]),
                    "input_vector": f"seed={RANDOM_SEED_HEX};game={g['game_id']}",
                    "model_id": "coin-v1"})
        out.append({"control_id": "S8362-FAVORITE", "game_id": g["game_id"],
                    "pick": favorite_pick(g["game_id"], g["away"], g["home"], rat),
                    "input_vector": f"S_{g['home']}={rat[g['home']]['strength']:.4f};"
                                    f"S_{g['away']}={rat[g['away']]['strength']:.4f}",
                    "model_id": MODEL_ID})
    return out

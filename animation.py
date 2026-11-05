# ============================================================
#  animation.py  –  State machine / timing controller
# ============================================================

import numpy as np
import config
from bezier import phase_progress, ease_in_out


class AnimationController:
    """
    Tracks elapsed time and exposes current animation state.
    Uses binary search on pre-sorted appear_times for O(log N) dot queries.
    """

    def __init__(self, cloud):
        self._cloud = cloud
        self._appear_times = cloud.appear_times   # sorted np.float32 array

    # ── Core query ───────────────────────────────────────────

    def visible_count(self, elapsed: float) -> int:
        """How many dots are visible at time `elapsed` seconds?"""
        return int(np.searchsorted(self._appear_times, elapsed, side="right"))

    # ── Phase helpers ─────────────────────────────────────────

    def message_alpha(self, elapsed: float) -> float:
        """0→1 opacity for the final message."""
        raw = phase_progress(elapsed, config.T_MSG_FADE_START, config.T_MSG_FADE_END)
        return ease_in_out(raw)

    def is_fully_bloomed(self, elapsed: float) -> bool:
        return elapsed >= config.T_BLOOM_END

    def is_complete(self, elapsed: float) -> bool:
        return elapsed >= config.T_TOTAL

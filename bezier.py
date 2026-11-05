# ============================================================
#  bezier.py  –  Geometric / math utilities
# ============================================================

import math
import numpy as np


def lerp(a: float, b: float, t: float) -> float:
    return a + (b - a) * t


def cubic_bezier_pt(p0, p1, p2, p3, t: float):
    """Return a single point on a cubic Bézier at parameter t."""
    p0, p1, p2, p3 = (np.asarray(p, float) for p in (p0, p1, p2, p3))
    return ((1 - t) ** 3 * p0
            + 3 * (1 - t) ** 2 * t * p1
            + 3 * (1 - t) * t ** 2 * p2
            + t ** 3 * p3)


def bezier_path(p0, p1, p2, p3, n: int = 200) -> np.ndarray:
    """Return (n, 2) array of evenly-spaced points along a cubic Bézier."""
    t_vals = np.linspace(0.0, 1.0, n)
    return np.array([cubic_bezier_pt(p0, p1, p2, p3, t) for t in t_vals])


def rotate_pt(x: float, y: float,
              cx: float, cy: float,
              angle_rad: float):
    """Rotate (x, y) around (cx, cy) by angle_rad."""
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    dx, dy = x - cx, y - cy
    return (cx + dx * cos_a - dy * sin_a,
            cy + dx * sin_a + dy * cos_a)


def ease_in_out(t: float) -> float:
    """Smooth-step easing (cubic)."""
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def phase_progress(elapsed: float, t_start: float, t_end: float) -> float:
    """Linear 0→1 progress within [t_start, t_end]."""
    if elapsed <= t_start:
        return 0.0
    if elapsed >= t_end:
        return 1.0
    return (elapsed - t_start) / (t_end - t_start)

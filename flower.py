# ============================================================
#  flower.py  –  Pre-computed dot geometry for the full lily
#
#  All positions + colours are calculated once at startup.
#  Dots are stored as compact numpy arrays for fast rendering.
# ============================================================

import math
import numpy as np

import config
from bezier import bezier_path, cubic_bezier_pt, rotate_pt


# ── Dot container (plain numpy arrays, no object per dot) ───
class DotCloud:
    """Holds all pre-computed dot data as contiguous numpy arrays."""

    def __init__(self):
        self._xs: list[float] = []
        self._ys: list[float] = []
        self._rs: list[float] = []
        self._gs: list[float] = []
        self._bs: list[float] = []
        self._ts: list[float] = []   # appear_time (seconds)

    # ── Dot insertion ────────────────────────────────────────

    def add(self, x: float, y: float,
            color: tuple, appear_time: float,
            rng: np.random.Generator,
            jitter: bool = True,
            brightness_var: bool = True):
        if jitter:
            x += rng.normal(0, config.DOT_JITTER)
            y += rng.normal(0, config.DOT_JITTER)
        bv = rng.uniform(0.72, 1.0) if brightness_var else 1.0
        r, g, b = color
        self._xs.append(x)
        self._ys.append(y)
        self._rs.append(r * bv)
        self._gs.append(g * bv)
        self._bs.append(b * bv)
        self._ts.append(appear_time)

    # ── Finalise into sorted numpy arrays ───────────────────

    def build(self):
        order = np.argsort(self._ts)
        self.xs    = np.array(self._xs, np.float32)[order]
        self.ys    = np.array(self._ys, np.float32)[order]
        self.colors = np.stack([
            np.array(self._rs, np.float32)[order],
            np.array(self._gs, np.float32)[order],
            np.array(self._bs, np.float32)[order],
        ], axis=1)   # (N, 3)
        self.appear_times = np.array(self._ts, np.float32)[order]

    @property
    def total(self) -> int:
        return len(self.appear_times)


# ── Main geometry class ─────────────────────────────────────

class FlowerGeometry:
    """Generates all dot data for the animated lily."""

    # Stem bezier control points (shared between stem & leaves)
    _STEM_P0 = (config.STEM_BASE_X,       config.STEM_BASE_Y)
    _STEM_P1 = (config.STEM_BASE_X - 18,  config.STEM_BASE_Y - 155)
    _STEM_P2 = (config.FLOWER_CTR_X + 12, config.FLOWER_CTR_Y + 165)
    _STEM_P3 = (config.FLOWER_CTR_X,      config.FLOWER_CTR_Y + 8)

    def __init__(self, seed: int = 42):
        self._rng = np.random.default_rng(seed)
        self._cloud = DotCloud()
        self._generate()
        self._cloud.build()

    @property
    def cloud(self) -> DotCloud:
        return self._cloud

    # ── Top-level generation ─────────────────────────────────

    def _generate(self):
        self._gen_stem()
        self._gen_leaves()
        self._gen_bud()
        self._gen_petals()
        self._gen_stamens()
        self._gen_center()

    # ── Stem ─────────────────────────────────────────────────

    def _gen_stem(self):
        p0, p1, p2, p3 = (
            self._STEM_P0, self._STEM_P1,
            self._STEM_P2, self._STEM_P3,
        )
        pts = bezier_path(p0, p1, p2, p3, n=280)
        n = len(pts)

        for i, (px, py) in enumerate(pts):
            t_stem = i / (n - 1)
            appear = (config.T_STEM_START
                      + t_stem * (config.T_STEM_END - config.T_STEM_START))

            # 3 dots per curve point: core + 2 width-spread
            for _ in range(3):
                dx = self._rng.uniform(-2.2, 2.2)
                self._cloud.add(px + dx, py, config.C_STEM_CORE,
                                appear, self._rng)

            # Occasional bright glow dot on the midline
            if self._rng.random() < 0.28:
                self._cloud.add(px, py, config.C_STEM_GLOW,
                                appear, self._rng)

    # ── Leaves ───────────────────────────────────────────────

    def _gen_leaves(self):
        """Two pairs of narrow lily leaves at different stem heights."""
        # (stem_t, angle_deg, length_factor, appear_offset)
        leaf_specs = [
            (0.22, -58, 0.88, 0.0),
            (0.22, +52, 0.82, 0.3),
            (0.50, -68, 1.00, 0.6),
            (0.50, +62, 0.95, 0.9),
        ]
        p0, p1, p2, p3 = (
            self._STEM_P0, self._STEM_P1,
            self._STEM_P2, self._STEM_P3,
        )

        for idx, (t_on_stem, angle_deg, l_fac, t_off) in enumerate(leaf_specs):
            stem_pt = cubic_bezier_pt(p0, p1, p2, p3, t_on_stem)
            bx, by = float(stem_pt[0]), float(stem_pt[1])

            leaf_start = config.T_LEAVES_START + t_off
            leaf_end   = leaf_start + 2.5

            self._gen_single_leaf(bx, by, angle_deg,
                                  config.LEAF_LENGTH * l_fac,
                                  leaf_start, leaf_end)

    def _gen_single_leaf(self, bx: float, by: float,
                         angle_deg: float, length: float,
                         t_start: float, t_end: float):
        angle_rad = math.radians(angle_deg)
        n_len = max(20, int(length / config.DOT_SPACING * 2.8))

        for i in range(n_len):
            t_leaf = i / (n_len - 1)

            # Position: droops slightly toward tip
            lx = bx + math.sin(angle_rad) * length * t_leaf
            ly = by - abs(math.cos(angle_rad)) * length * t_leaf * 0.72

            # Width profile: sin-peak around 40% of length
            half_w = 11 * (math.sin(math.pi * t_leaf)) ** 0.65

            n_w = 6
            for j in range(n_w):
                v = (j / (n_w - 1)) * 2 - 1   # -1 → +1

                # Offset perpendicular to leaf axis
                perp_x = -math.cos(angle_rad) * v * half_w
                perp_y = -math.sin(angle_rad) * v * half_w * 0.35

                wx = lx + perp_x
                wy = ly + perp_y

                edge = abs(v)

                # Midrib highlight
                if edge < 0.25:
                    color = config.C_LEAF_GLOW
                else:
                    r = config.C_LEAF_CORE[0] * (1 - edge * 0.25)
                    g = config.C_LEAF_CORE[1] * (1 - edge * 0.18)
                    b = config.C_LEAF_CORE[2] * (1 - edge * 0.25)
                    color = (r, g, b)

                appear = t_start + t_leaf * (t_end - t_start)
                self._cloud.add(wx, wy, color, appear, self._rng)

    # ── Bud ──────────────────────────────────────────────────

    def _gen_bud(self):
        cx, cy = config.FLOWER_CTR_X, config.FLOWER_CTR_Y
        # 3 upright bud segments, tightly grouped
        bud_angles = [-20, 0, 20]

        t_start = config.T_BUD_START
        t_end   = config.T_BUD_END

        for b_idx, angle_deg in enumerate(bud_angles):
            angle_rad = math.radians(angle_deg)
            n_len = int(config.BUD_LENGTH / config.DOT_SPACING * 3)
            n_w   = 8

            for i in range(n_len):
                t_p = i / (n_len - 1)
                hw = config.BUD_MAX_W * (math.sin(math.pi * t_p)) ** 0.65

                for j in range(n_w):
                    v = (j / (n_w - 1)) * 2 - 1

                    local_x = v * hw
                    local_y = -t_p * config.BUD_LENGTH

                    wx, wy = rotate_pt(local_x, local_y, 0, 0, angle_rad)
                    wx += cx
                    wy += cy

                    t_col = t_p * 0.7 + abs(v) * 0.3
                    r = config.C_BUD_INNER[0] + (config.C_BUD_OUTER[0] - config.C_BUD_INNER[0]) * t_col
                    g = config.C_BUD_INNER[1] + (config.C_BUD_OUTER[1] - config.C_BUD_INNER[1]) * t_col
                    b = config.C_BUD_INNER[2] + (config.C_BUD_OUTER[2] - config.C_BUD_INNER[2]) * t_col

                    appear = t_start + (t_p * 0.7 + b_idx * 0.12) * (t_end - t_start)
                    appear = min(appear, t_end)
                    self._cloud.add(wx, wy, (r, g, b), appear, self._rng)

    # ── Petals ───────────────────────────────────────────────

    def _gen_petals(self):
        cx, cy = config.FLOWER_CTR_X, config.FLOWER_CTR_Y

        # (angle_deg, length_factor, width_factor, curve, t_offset)
        # Lily front-view: upper pair + side pair + lower pair
        petal_specs = [
            (-28,  1.00, 1.00,  0.38, 0.00),   # upper-left
            ( 32,  1.04, 1.00, -0.38, 0.08),   # upper-right
            (-92,  0.94, 0.90,  0.28, 0.14),   # left
            ( 96,  0.94, 0.90, -0.28, 0.20),   # right
            (-148, 0.98, 1.00,  0.42, 0.26),   # lower-left
            ( 152, 0.98, 1.00, -0.42, 0.33),   # lower-right
        ]

        t_start = config.T_BLOOM_START
        t_end   = config.T_BLOOM_END
        bloom_dur = t_end - t_start

        for p_idx, (angle_deg, l_fac, w_fac, curve, t_off) in enumerate(petal_specs):
            angle_rad   = math.radians(angle_deg)
            pet_length  = config.PETAL_LENGTH * l_fac
            pet_max_w   = config.PETAL_MAX_W  * w_fac

            pet_t_start = t_start + t_off * bloom_dur
            pet_t_end   = t_end

            n_len = int(pet_length / config.DOT_SPACING * 3.2)
            n_w   = 12

            for i in range(n_len):
                t_p = i / (n_len - 1)

                # Width profile (peaks at ~38 %)
                hw = pet_max_w * (t_p ** 0.52) * ((1 - t_p) ** 0.32)
                hw = max(hw, 0.0)

                # Lateral curve: petal sweeps outward at mid-length
                x_curve = curve * pet_max_w * math.sin(math.pi * t_p) * t_p

                # Slight reflexing at tip (3-D fold-back effect)
                reflex_y = 18 * (t_p ** 2.5) * math.sin(math.pi * t_p)

                for j in range(n_w):
                    v = (j / (n_w - 1)) * 2 - 1

                    # Wavy petal edges
                    edge_wave = math.sin(t_p * math.pi * 2.5) * 1.8 * t_p * abs(v)

                    local_x = v * hw + x_curve + edge_wave * (1 if v > 0 else -1)
                    local_y = -t_p * pet_length + reflex_y

                    wx, wy = rotate_pt(local_x, local_y, 0, 0, angle_rad)
                    wx += cx
                    wy += cy

                    # ── colour gradient ──────────────────────
                    edge = abs(v)
                    t_col = t_p * 0.65 + edge * 0.35

                    r = config.C_PET_INNER[0] + (config.C_PET_OUTER[0] - config.C_PET_INNER[0]) * t_col
                    g = config.C_PET_INNER[1] + (config.C_PET_OUTER[1] - config.C_PET_INNER[1]) * t_col
                    b = config.C_PET_INNER[2] + (config.C_PET_OUTER[2] - config.C_PET_INNER[2]) * t_col

                    # Blue-violet edge highlight
                    if edge > 0.72:
                        eb = (edge - 0.72) / 0.28
                        r = r * (1 - eb) + config.C_PET_EDGE[0] * eb
                        g = g * (1 - eb) + config.C_PET_EDGE[1] * eb
                        b = b * (1 - eb) + config.C_PET_EDGE[2] * eb

                    appear = pet_t_start + t_p * 0.55 * (pet_t_end - pet_t_start)
                    self._cloud.add(wx, wy, (r, g, b), appear, self._rng)

    # ── Stamens ──────────────────────────────────────────────

    def _gen_stamens(self):
        cx, cy = config.FLOWER_CTR_X, config.FLOWER_CTR_Y
        stamen_length = 68
        stamen_angles = [0, 60, 120, 180, 240, 300]

        t_start = config.T_STAMENS_START
        t_end   = config.T_STAMENS_END

        for idx, angle_deg in enumerate(stamen_angles):
            angle_rad = math.radians(angle_deg)
            n_pts = int(stamen_length / config.DOT_SPACING * 2)

            for i in range(n_pts):
                t_st = i / (n_pts - 1)
                local_y = -t_st * stamen_length

                wx, wy = rotate_pt(0, local_y, 0, 0, angle_rad)
                wx += cx
                wy += cy

                brightness = 0.45 + t_st * 0.55
                r, g, b = config.C_STAMEN
                appear = t_start + idx * 0.12 + t_st * 0.35
                self._cloud.add(wx, wy,
                                (r * brightness, g * brightness, b * brightness),
                                appear, self._rng)

            # Anther cluster at tip
            tip_wx, tip_wy = rotate_pt(0, -stamen_length, 0, 0, angle_rad)
            tip_wx += cx
            tip_wy += cy

            for _ in range(10):
                ax = tip_wx + self._rng.uniform(-3.5, 3.5)
                ay = tip_wy + self._rng.uniform(-3.5, 3.5)
                appear = t_end - 0.4 + idx * 0.06
                self._cloud.add(ax, ay, config.C_ANTHER,
                                appear, self._rng, jitter=False)

    # ── Centre pistil ────────────────────────────────────────

    def _gen_center(self):
        cx, cy = config.FLOWER_CTR_X, config.FLOWER_CTR_Y

        for _ in range(45):
            x = cx + self._rng.uniform(-7, 7)
            y = cy + self._rng.uniform(-7, 7)
            dist = math.hypot(x - cx, y - cy)
            br = max(0.3, 1.0 - dist / 9)
            r, g, b = config.C_CENTER
            appear = config.T_BLOOM_START + 2.5
            self._cloud.add(x, y, (r * br, g * br, b * br),
                            appear, self._rng, jitter=False)

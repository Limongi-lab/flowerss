import math
import numpy as np

import config
from bezier import bezier_path, cubic_bezier_pt, rotate_pt


class DotCloud:
    def __init__(self):
        self._xs = []
        self._ys = []
        self._rs = []
        self._gs = []
        self._bs = []
        self._ts = []

    def add(self, x, y, color, appear_time, rng, jitter=True, brightness_var=True):
        if jitter:
            x += rng.normal(0, config.DOT_JITTER)
            y += rng.normal(0, config.DOT_JITTER)
        bv = rng.uniform(0.70, 1.0) if brightness_var else 1.0
        r, g, b = color
        self._xs.append(x)
        self._ys.append(y)
        self._rs.append(r * bv)
        self._gs.append(g * bv)
        self._bs.append(b * bv)
        self._ts.append(appear_time)

    def build(self):
        order = np.argsort(self._ts)
        self.xs    = np.array(self._xs, np.float32)[order]
        self.ys    = np.array(self._ys, np.float32)[order]
        self.colors = np.stack([
            np.array(self._rs, np.float32)[order],
            np.array(self._gs, np.float32)[order],
            np.array(self._bs, np.float32)[order],
        ], axis=1)
        self.appear_times = np.array(self._ts, np.float32)[order]

    @property
    def total(self):
        return len(self.appear_times)


class FlowerGeometry:
    _STEM_P0 = (config.STEM_BASE_X,       config.STEM_BASE_Y)
    _STEM_P1 = (config.STEM_BASE_X - 20,  config.STEM_BASE_Y - 160)
    _STEM_P2 = (config.FLOWER_CTR_X + 14, config.FLOWER_CTR_Y + 170)
    _STEM_P3 = (config.FLOWER_CTR_X,      config.FLOWER_CTR_Y + 10)

    def __init__(self, seed=42):
        self._rng = np.random.default_rng(seed)
        self._cloud = DotCloud()
        self._generate()
        self._cloud.build()

    @property
    def cloud(self):
        return self._cloud

    def _generate(self):
        self._gen_stem()
        self._gen_leaves()
        self._gen_bud()
        self._gen_petals()
        self._gen_stamens()
        self._gen_center_glow()

    def _gen_stem(self):
        p0 = np.array(self._STEM_P0)
        p1 = np.array(self._STEM_P1)
        p2 = np.array(self._STEM_P2)
        p3 = np.array(self._STEM_P3)
        pts = bezier_path(p0, p1, p2, p3, n=300)
        n = len(pts)

        for i, (px, py) in enumerate(pts):
            t_stem = i / (n - 1)
            appear = config.T_STEM_START + t_stem * (config.T_STEM_END - config.T_STEM_START)

            for _ in range(3):
                dx = self._rng.uniform(-1.8, 1.8)
                self._cloud.add(float(px + dx), float(py), config.C_STEM_CORE, appear, self._rng)

            if self._rng.random() < 0.25:
                self._cloud.add(float(px), float(py), config.C_STEM_GLOW, appear, self._rng)

    def _gen_leaves(self):
        p0 = np.array(self._STEM_P0)
        p1 = np.array(self._STEM_P1)
        p2 = np.array(self._STEM_P2)
        p3 = np.array(self._STEM_P3)

        leaf_specs = [
            (0.55, -62, 0.95, 0.0),
            (0.55, +55, 0.90, 0.3),
            (0.32, -72, 0.80, 0.6),
            (0.32, +58, 0.75, 0.9),
        ]

        for idx, (t_on_stem, angle_deg, l_fac, t_off) in enumerate(leaf_specs):
            pt = cubic_bezier_pt(p0, p1, p2, p3, t_on_stem)
            bx, by = float(pt[0]), float(pt[1])
            leaf_start = config.T_LEAVES_START + t_off
            leaf_end   = leaf_start + 2.8
            self._gen_single_leaf(bx, by, angle_deg, config.LEAF_LENGTH * l_fac, leaf_start, leaf_end)

    def _gen_single_leaf(self, bx, by, angle_deg, length, t_start, t_end):
        angle_rad = math.radians(angle_deg)
        n_len = max(22, int(length / config.DOT_SPACING * 3.0))

        for i in range(n_len):
            t_leaf = i / (n_len - 1)
            lx = bx + math.sin(angle_rad) * length * t_leaf
            ly = by - abs(math.cos(angle_rad)) * length * t_leaf * 0.68
            half_w = 10.0 * (math.sin(math.pi * t_leaf)) ** 0.6

            for j in range(6):
                v = (j / 5) * 2 - 1
                perp_x = -math.cos(angle_rad) * v * half_w
                perp_y = -math.sin(angle_rad) * v * half_w * 0.30
                wx = lx + perp_x
                wy = ly + perp_y
                edge = abs(v)

                if edge < 0.22:
                    color = (config.C_LEAF_GLOW[0]*0.60, config.C_LEAF_GLOW[1]*0.60, config.C_LEAF_GLOW[2]*0.60)
                else:
                    r = config.C_LEAF_CORE[0] * (1 - edge * 0.20)
                    g = config.C_LEAF_CORE[1] * (1 - edge * 0.14)
                    b = config.C_LEAF_CORE[2] * (1 - edge * 0.20)
                    color = (r, g, b)

                appear = t_start + t_leaf * (t_end - t_start)
                self._cloud.add(wx, wy, color, appear, self._rng)

    def _gen_bud(self):
        cx, cy = config.FLOWER_CTR_X, config.FLOWER_CTR_Y
        t_start = config.T_BUD_START
        t_end   = config.T_BUD_END

        for b_idx, angle_deg in enumerate([-22, 0, 22]):
            angle_rad = math.radians(angle_deg)
            n_len = int(config.BUD_LENGTH / config.DOT_SPACING * 3.5)

            for i in range(n_len):
                t_p = i / (n_len - 1)
                hw = config.BUD_MAX_W * (math.sin(math.pi * t_p)) ** 0.60

                for j in range(8):
                    v = (j / 7) * 2 - 1
                    wx, wy = rotate_pt(v * hw, -t_p * config.BUD_LENGTH, 0, 0, angle_rad)
                    wx += cx
                    wy += cy

                    t_col = t_p * 0.68 + abs(v) * 0.32
                    r = config.C_BUD_INNER[0] + (config.C_BUD_OUTER[0] - config.C_BUD_INNER[0]) * t_col
                    g = config.C_BUD_INNER[1] + (config.C_BUD_OUTER[1] - config.C_BUD_INNER[1]) * t_col
                    b = config.C_BUD_INNER[2] + (config.C_BUD_OUTER[2] - config.C_BUD_INNER[2]) * t_col

                    appear = min(t_start + (t_p * 0.68 + b_idx * 0.11) * (t_end - t_start), t_end)
                    self._cloud.add(wx, wy, (r, g, b), appear, self._rng)

    def _gen_petals(self):
        cx, cy = config.FLOWER_CTR_X, config.FLOWER_CTR_Y

        petal_specs = [
            (-25,  1.00, 1.00,  0.35, 0.00),
            ( 30,  1.05, 1.00, -0.35, 0.09),
            (-90,  0.92, 0.90,  0.25, 0.16),
            ( 95,  0.92, 0.90, -0.25, 0.22),
            (-145, 0.98, 0.95,  0.40, 0.28),
            ( 150, 0.97, 0.95, -0.40, 0.35),
        ]

        t_start   = config.T_BLOOM_START
        t_end     = config.T_BLOOM_END
        bloom_dur = t_end - t_start

        for p_idx, (angle_deg, l_fac, w_fac, curve, t_off) in enumerate(petal_specs):
            angle_rad  = math.radians(angle_deg)
            pet_length = config.PETAL_LENGTH * l_fac
            pet_max_w  = config.PETAL_MAX_W  * w_fac
            pet_t_start = t_start + t_off * bloom_dur
            pet_t_end   = t_end
            n_len = int(pet_length / config.DOT_SPACING * 3.5)

            for i in range(n_len):
                t_p = i / (n_len - 1)
                hw = max(0.0, pet_max_w * (t_p ** 0.50) * ((1 - t_p) ** 0.30))
                x_curve = curve * pet_max_w * math.sin(math.pi * t_p) * t_p
                reflex_y = 20.0 * (t_p ** 2.2) * math.sin(math.pi * t_p)

                for j in range(13):
                    v = (j / 12) * 2 - 1
                    edge_wave = math.sin(t_p * math.pi * 2.2) * 2.0 * t_p * (1 if abs(v) > 0.55 else 0)
                    local_x = v * hw + x_curve + edge_wave * (1 if v > 0 else -1)
                    local_y = -t_p * pet_length + reflex_y

                    wx, wy = rotate_pt(local_x, local_y, 0, 0, angle_rad)
                    wx += cx
                    wy += cy

                    edge = abs(v)
                    t_col = t_p * 0.60 + edge * 0.40

                    r = config.C_PET_INNER[0] + (config.C_PET_OUTER[0] - config.C_PET_INNER[0]) * t_col
                    g = config.C_PET_INNER[1] + (config.C_PET_OUTER[1] - config.C_PET_INNER[1]) * t_col
                    b = config.C_PET_INNER[2] + (config.C_PET_OUTER[2] - config.C_PET_INNER[2]) * t_col

                    if edge > 0.75:
                        eb = (edge - 0.75) / 0.25
                        r = r*(1-eb) + config.C_PET_EDGE[0]*eb
                        g = g*(1-eb) + config.C_PET_EDGE[1]*eb
                        b = b*(1-eb) + config.C_PET_EDGE[2]*eb

                    appear = pet_t_start + t_p * 0.52 * (pet_t_end - pet_t_start)
                    self._cloud.add(wx, wy, (r, g, b), appear, self._rng)

    def _gen_stamens(self):
        cx, cy = config.FLOWER_CTR_X, config.FLOWER_CTR_Y
        stamen_length = 72
        t_start = config.T_STAMENS_START
        t_end   = config.T_STAMENS_END

        for idx, angle_deg in enumerate([0, 60, 120, 180, 240, 300]):
            angle_rad = math.radians(angle_deg)
            n_pts = int(stamen_length / config.DOT_SPACING * 2.2)

            for i in range(n_pts):
                t_st = i / (n_pts - 1)
                wx, wy = rotate_pt(0, -t_st * stamen_length, 0, 0, angle_rad)
                brightness = 0.40 + t_st * 0.60
                r, g, b = config.C_STAMEN
                appear = t_start + idx * 0.13 + t_st * 0.38
                self._cloud.add(wx + cx, wy + cy, (r*brightness, g*brightness, b*brightness), appear, self._rng)

            tip_wx, tip_wy = rotate_pt(0, -stamen_length, 0, 0, angle_rad)
            for _ in range(12):
                ax = tip_wx + cx + self._rng.uniform(-3.8, 3.8)
                ay = tip_wy + cy + self._rng.uniform(-3.8, 3.8)
                appear = t_end - 0.5 + idx * 0.07
                self._cloud.add(ax, ay, config.C_ANTHER, appear, self._rng, jitter=False)

    def _gen_center_glow(self):
        cx, cy = config.FLOWER_CTR_X, config.FLOWER_CTR_Y
        for _ in range(60):
            x = cx + self._rng.uniform(-8, 8)
            y = cy + self._rng.uniform(-8, 8)
            dist = math.hypot(x - cx, y - cy)
            br = max(0.25, 1.0 - dist / 10.0)
            r, g, b = config.C_CENTER
            appear = config.T_BLOOM_START + 2.0
            self._cloud.add(x, y, (r*br, g*br, b*br), appear, self._rng, jitter=False)

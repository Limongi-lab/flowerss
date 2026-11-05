# ============================================================
#  renderer.py  –  Frame rendering via numpy + PIL
#
#  Technique:
#   1. Additive scatter – each dot adds its colour to a float buffer.
#   2. Reinhard tone-mapping + gamma, so overlapping dots "bloom".
#   3. A single PIL GaussianBlur pass creates the neon-glow halo.
#   4. Blurred and sharp layers are composited additively.
#   5. Message text is drawn on top via RGBA overlay.
# ============================================================

import numpy as np
from PIL import Image, ImageFilter, ImageDraw, ImageFont
import config


_FONT_PATHS = [
    "C:/Windows/Fonts/Georgia.ttf",
    "C:/Windows/Fonts/cambria.ttc",
    "C:/Windows/Fonts/Palatino.ttf",
    "C:/Windows/Fonts/times.ttf",
    "C:/Windows/Fonts/calibri.ttf",
]


def _load_font(size: int) -> ImageFont.FreeTypeFont:
    for path in _FONT_PATHS:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


class Renderer:
    def __init__(self, width: int, height: int):
        self.w = width
        self.h = height
        self._font = _load_font(config.MESSAGE_FONT_SIZE)
        self._frame = np.zeros((height, width, 3), dtype=np.float32)

        # Static background: near-black + faint star-field
        self._bg = np.zeros((height, width, 3), dtype=np.float32)
        self._build_background()

    # ── Background ───────────────────────────────────────────

    def _build_background(self):
        rng = np.random.default_rng(7)
        # Faint vignette: slightly lighter at centre
        cy, cx = self.h / 2, self.w / 2
        Y, X = np.mgrid[0:self.h, 0:self.w]
        dist = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)
        max_d = np.sqrt(cx ** 2 + cy ** 2)
        vignette = (1.0 - dist / max_d) * 0.012
        self._bg[:, :, 2] += vignette.astype(np.float32)   # blue tint at centre

        # Stars
        n = 140
        xs = rng.integers(0, self.w, n)
        ys = rng.integers(0, self.h, n)
        brs = rng.uniform(0.025, 0.11, n).astype(np.float32)
        for x, y, br in zip(xs, ys, brs):
            self._bg[y, x] = [br * 0.9, br * 0.9, br * 1.15]

    # ── Main render ──────────────────────────────────────────

    def render(self,
               cloud,             # DotCloud with .xs .ys .colors .appear_times
               visible_count: int,
               particles: list,
               message_alpha: float) -> Image.Image:
        """Render one frame, return a PIL RGB Image."""

        # Reset to background
        frame = self._frame
        np.copyto(frame, self._bg)

        # ── Scatter flower dots ───────────────────────────────
        if visible_count > 0:
            xs = cloud.xs[:visible_count].astype(np.int32)
            ys = cloud.ys[:visible_count].astype(np.int32)
            cols = cloud.colors[:visible_count]           # (N, 3) float32

            # Clip to canvas bounds
            mask = (xs >= 0) & (xs < self.w) & (ys >= 0) & (ys < self.h)
            xs, ys, cols = xs[mask], ys[mask], cols[mask]

            # Primary pixel
            np.add.at(frame, (ys, xs), cols)

            # +1-pixel soft spread (makes dots visible at zoom-out)
            spread_w = 0.30
            for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxs = (xs + dx).clip(0, self.w - 1)
                nys = (ys + dy).clip(0, self.h - 1)
                np.add.at(frame, (nys, nxs), cols * spread_w)

        # ── Scatter particles ─────────────────────────────────
        for px, py, r, g, b in particles:
            ix, iy = int(px), int(py)
            if 0 <= ix < self.w and 0 <= iy < self.h:
                frame[iy, ix, 0] += r * 2.5
                frame[iy, ix, 1] += g * 2.5
                frame[iy, ix, 2] += b * 2.5

        # ── Tone-map + gamma ──────────────────────────────────
        # Reinhard: out = x / (1 + x)  → prevents hard clipping, creates bloom
        display = frame / (1.0 + frame)

        # Gamma 2.2
        display = np.power(display.clip(0.0, 1.0), 1.0 / 2.2)

        base_arr = (display * 255.0).astype(np.uint8)
        base_img = Image.fromarray(base_arr, "RGB")

        # ── Glow pass (single PIL blur, then additive blend) ──
        glow_img = base_img.filter(
            ImageFilter.GaussianBlur(radius=config.GLOW_BLUR_RADIUS)
        )
        glow_arr = np.array(glow_img, dtype=np.float32) / 255.0
        base_f   = base_arr.astype(np.float32) / 255.0

        blended = (base_f + glow_arr * config.GLOW_STRENGTH).clip(0.0, 1.0)
        result_img = Image.fromarray(
            (blended * 255.0).astype(np.uint8), "RGB"
        )

        # ── Message ───────────────────────────────────────────
        if message_alpha > 0.0:
            result_img = self._draw_message(result_img, message_alpha)

        return result_img

    # ── Message overlay ──────────────────────────────────────

    def _draw_message(self, img: Image.Image, alpha: float) -> Image.Image:
        overlay = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        text = config.MESSAGE_TEXT
        r, g, b = config.C_MESSAGE
        a_int = int(alpha * 230)

        # Measure text
        try:
            bbox = draw.textbbox((0, 0), text, font=self._font)
            tw = bbox[2] - bbox[0]
        except AttributeError:
            tw, _ = draw.textsize(text, font=self._font)

        x = (self.w - tw) // 2
        y = int(self.h * 0.84)

        # Soft glow behind text: draw it wider + dimmer first
        glow_a = int(a_int * 0.35)
        for ox, oy in ((-2, 0), (2, 0), (0, -2), (0, 2),
                        (-1, -1), (1, -1), (-1, 1), (1, 1)):
            draw.text(
                (x + ox, y + oy), text,
                font=self._font,
                fill=(int(r * 255), int(g * 255), int(b * 255), glow_a),
            )

        # Sharp text
        draw.text(
            (x, y), text,
            font=self._font,
            fill=(int(r * 255), int(g * 255), int(b * 255), a_int),
        )

        base_rgba = img.convert("RGBA")
        result = Image.alpha_composite(base_rgba, overlay)
        return result.convert("RGB")

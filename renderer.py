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

_NAME_FONT_PATHS = [
    "C:/Windows/Fonts/seguisym.ttf",
    "C:/Windows/Fonts/seguiemj.ttf",
    "C:/Windows/Fonts/segoeui.ttf",
    "C:/Windows/Fonts/Georgia.ttf",
    "C:/Windows/Fonts/calibri.ttf",
]


def _load_font(size, paths=None):
    for path in (paths or _FONT_PATHS):
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


class Renderer:
    def __init__(self, width, height):
        self.w = width
        self.h = height
        self._font_msg  = _load_font(config.MESSAGE_FONT_SIZE)
        self._font_name = _load_font(config.NAME_FONT_SIZE, _NAME_FONT_PATHS)
        self._frame = np.zeros((height, width, 3), dtype=np.float32)
        self._bg = np.zeros((height, width, 3), dtype=np.float32)
        self._build_background()

    def _build_background(self):
        rng = np.random.default_rng(7)
        self._bg[:, :, :] = 0.0
        n = 110
        xs  = rng.integers(0, self.w, n)
        ys  = rng.integers(0, self.h, n)
        brs = rng.uniform(0.015, 0.075, n).astype(np.float32)
        for x, y, br in zip(xs, ys, brs):
            self._bg[y, x] = [br * 0.88, br * 0.88, br * 1.1]

    def render(self, cloud, visible_count, particles, message_alpha, name_alpha=0.0, glow_boost=1.0):
        frame = self._frame
        np.copyto(frame, self._bg)

        if visible_count > 0:
            xs   = cloud.xs[:visible_count].astype(np.int32)
            ys   = cloud.ys[:visible_count].astype(np.int32)
            cols = cloud.colors[:visible_count]

            mask = (xs >= 0) & (xs < self.w) & (ys >= 0) & (ys < self.h)
            xs, ys, cols = xs[mask], ys[mask], cols[mask]

            np.add.at(frame, (ys, xs), cols)

            for dy, dx in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                nxs = (xs + dx).clip(0, self.w - 1)
                nys = (ys + dy).clip(0, self.h - 1)
                np.add.at(frame, (nys, nxs), cols * 0.28)

            for dy, dx in ((-1, -1), (-1, 1), (1, -1), (1, 1)):
                nxs = (xs + dx).clip(0, self.w - 1)
                nys = (ys + dy).clip(0, self.h - 1)
                np.add.at(frame, (nys, nxs), cols * 0.14)

        for px, py, r, g, b in particles:
            ix, iy = int(px), int(py)
            if 0 <= ix < self.w and 0 <= iy < self.h:
                frame[iy, ix, 0] += r * 2.5
                frame[iy, ix, 1] += g * 2.5
                frame[iy, ix, 2] += b * 2.5

        display = frame / (1.0 + frame)
        display = np.power(display.clip(0.0, 1.0), 1.0 / 2.2)

        base_arr = (display * 255.0).astype(np.uint8)
        base_img = Image.fromarray(base_arr, "RGB")

        glow_img = base_img.filter(ImageFilter.GaussianBlur(radius=config.GLOW_BLUR_RADIUS))
        glow_arr = np.array(glow_img, dtype=np.float32) / 255.0
        base_f   = base_arr.astype(np.float32) / 255.0

        strength = config.GLOW_STRENGTH * glow_boost
        blended  = (base_f + glow_arr * strength).clip(0.0, 1.0)
        result_img = Image.fromarray((blended * 255.0).astype(np.uint8), "RGB")

        if message_alpha > 0.0 or name_alpha > 0.0:
            result_img = self._draw_overlays(result_img, message_alpha, name_alpha)

        return result_img

    def _draw_overlays(self, img, message_alpha, name_alpha):
        overlay = Image.new("RGBA", (self.w, self.h), (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        if message_alpha > 0.0:
            self._draw_text_centered(
                draw,
                config.MESSAGE_TEXT,
                self._font_msg,
                config.C_MESSAGE,
                y_frac=0.87,
                alpha=message_alpha,
            )

        if name_alpha > 0.0:
            self._draw_name_corner(draw, name_alpha)

        base_rgba = img.convert("RGBA")
        result = Image.alpha_composite(base_rgba, overlay)
        return result.convert("RGB")

    def _draw_text_centered(self, draw, text, font, color, y_frac, alpha):
        r, g, b = color
        a_int = int(alpha * 230)

        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            tw = bbox[2] - bbox[0]
        except AttributeError:
            tw, _ = draw.textsize(text, font=font)

        x = (self.w - tw) // 2
        y = int(self.h * y_frac)

        glow_a = int(a_int * 0.35)
        for ox, oy in ((-2,0),(2,0),(0,-2),(0,2),(-1,-1),(1,-1),(-1,1),(1,1)):
            draw.text((x+ox, y+oy), text, font=font, fill=(int(r*255), int(g*255), int(b*255), glow_a))

        draw.text((x, y), text, font=font, fill=(int(r*255), int(g*255), int(b*255), a_int))

    def _draw_name_corner(self, draw, alpha):
        text = config.NAME_TEXT
        font = self._font_name
        r, g, b = config.C_NAME
        a_int = int(alpha * 180)

        try:
            bbox = draw.textbbox((0, 0), text, font=font)
            tw = bbox[2] - bbox[0]
            th = bbox[3] - bbox[1]
        except AttributeError:
            tw, th = draw.textsize(text, font=font)

        x = self.w - tw - 18
        y = self.h - th - 18

        glow_a = int(a_int * 0.4)
        for ox, oy in ((-2,0),(2,0),(0,-2),(0,2)):
            draw.text((x+ox, y+oy), text, font=font, fill=(int(r*255), int(g*255), int(b*255), glow_a))

        draw.text((x, y), text, font=font, fill=(int(r*255), int(g*255), int(b*255), a_int))

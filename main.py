import tkinter as tk
from PIL import ImageTk
import time
import math

import config
from flower import FlowerGeometry
from particles import ParticleSystem
from renderer import Renderer
from animation import AnimationController


class FlowerApp:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title(config.TITLE)
        self.root.configure(bg=config.BG_HEX)
        self.root.resizable(False, False)

        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = max(0, (sw - config.WIDTH)  // 2)
        y = max(0, (sh - config.HEIGHT) // 2)
        self.root.geometry(f"{config.WIDTH}x{config.HEIGHT}+{x}+{y}")

        self._canvas = tk.Canvas(
            self.root,
            width=config.WIDTH,
            height=config.HEIGHT,
            bg=config.BG_HEX,
            highlightthickness=0,
        )
        self._canvas.pack()
        self._canvas_item = self._canvas.create_image(0, 0, anchor="nw")
        self._photo = None

        self._flower     = None
        self._particles  = None
        self._renderer   = None
        self._controller = None
        self._cloud      = None
        self._start_time = None
        self._frame_ms   = max(1, int(1000 / config.FPS))

        self.root.bind("<Escape>", lambda _: self.root.destroy())
        self.root.bind("<q>",      lambda _: self.root.destroy())

    def run(self):
        self.root.after(80, self._init_systems)
        self.root.mainloop()

    def _init_systems(self):
        self._flower     = FlowerGeometry()
        self._cloud      = self._flower.cloud
        self._particles  = ParticleSystem()
        self._renderer   = Renderer(config.WIDTH, config.HEIGHT)
        self._controller = AnimationController(self._cloud)
        self._start_time = time.perf_counter()
        self._tick()

    def _tick(self):
        elapsed = time.perf_counter() - self._start_time

        breathe_phase = max(0.0, elapsed - config.T_BLOOM_END)
        glow_boost = 1.0 + 0.08 * math.sin(breathe_phase * math.pi * 0.45)

        self._particles.update(1.0 / config.FPS, elapsed)

        n_visible   = self._controller.visible_count(elapsed)
        part_data   = self._particles.get_render_data()
        msg_alpha   = self._controller.message_alpha(elapsed)
        name_alpha  = self._controller.name_alpha(elapsed)

        frame_img = self._renderer.render(
            self._cloud,
            n_visible,
            part_data,
            msg_alpha,
            name_alpha=name_alpha,
            glow_boost=glow_boost,
        )

        photo = ImageTk.PhotoImage(frame_img)
        self._canvas.itemconfig(self._canvas_item, image=photo)
        self._photo = photo

        self.root.after(self._frame_ms, self._tick)


def main():
    app = FlowerApp()
    app.run()


if __name__ == "__main__":
    main()

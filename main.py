# ============================================================
#  main.py  –  Application entry point
#
#  Creates the tkinter window, runs the animation loop.
#  No console window is shown when launched as .pyw or built
#  with PyInstaller --noconsole.
# ============================================================

import tkinter as tk
from PIL import ImageTk
import time

import config
from flower import FlowerGeometry
from particles import ParticleSystem
from renderer import Renderer
from animation import AnimationController


class FlowerApp:
    """Main application: wires geometry, particles, renderer and tkinter."""

    def __init__(self):
        # ── Window ───────────────────────────────────────────
        self.root = tk.Tk()
        self.root.title(config.TITLE)
        self.root.configure(bg=config.BG_HEX)
        self.root.resizable(False, False)

        # Remove default window decorations feel: minimal chrome
        # (keep the standard title bar so the user can move/close)

        # Centre on screen
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = max(0, (sw - config.WIDTH)  // 2)
        y = max(0, (sh - config.HEIGHT) // 2)
        self.root.geometry(f"{config.WIDTH}x{config.HEIGHT}+{x}+{y}")

        # Canvas — the only widget
        self._canvas = tk.Canvas(
            self.root,
            width=config.WIDTH,
            height=config.HEIGHT,
            bg=config.BG_HEX,
            highlightthickness=0,
        )
        self._canvas.pack()
        self._canvas_item = self._canvas.create_image(0, 0, anchor="nw")
        self._photo = None   # keep reference to prevent GC

        # ── Systems ───────────────────────────────────────────
        # Pre-compute all flower dot geometry (runs once, ~0.5-1 s)
        self._flower = FlowerGeometry()
        cloud = self._flower.cloud

        self._particles  = ParticleSystem()
        self._renderer   = Renderer(config.WIDTH, config.HEIGHT)
        self._controller = AnimationController(cloud)
        self._cloud      = cloud

        # ── State ─────────────────────────────────────────────
        self._start_time: float | None = None
        self._frame_ms = max(1, int(1000 / config.FPS))

        # Keybindings
        self.root.bind("<Escape>", lambda _: self.root.destroy())

    # ── Entry point ──────────────────────────────────────────

    def run(self):
        self._start_time = time.perf_counter()
        self._tick()
        self.root.mainloop()

    # ── Animation loop ────────────────────────────────────────

    def _tick(self):
        elapsed = time.perf_counter() - self._start_time

        # Update particle simulation
        self._particles.update(1.0 / config.FPS, elapsed)

        # Query animation state
        n_visible  = self._controller.visible_count(elapsed)
        part_data  = self._particles.get_render_data()
        msg_alpha  = self._controller.message_alpha(elapsed)

        # Render
        frame_img = self._renderer.render(
            self._cloud,
            n_visible,
            part_data,
            msg_alpha,
        )

        # Push to canvas
        photo = ImageTk.PhotoImage(frame_img)
        self._canvas.itemconfig(self._canvas_item, image=photo)
        self._photo = photo   # prevent garbage collection

        # Schedule next frame
        self.root.after(self._frame_ms, self._tick)


# ── Entry ─────────────────────────────────────────────────────

def main():
    app = FlowerApp()
    app.run()


if __name__ == "__main__":
    main()

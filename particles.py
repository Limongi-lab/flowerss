import math
import numpy as np
import config


class Particle:
    __slots__ = ["x", "y", "vx", "vy", "life", "max_life", "color"]

    def __init__(self, x, y, vx, vy, life, color):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.life = life
        self.max_life = life
        self.color = color


class ParticleSystem:
    def __init__(self, seed=99):
        self._rng = np.random.default_rng(seed)
        self._particles = []
        self._emit_timer = 0.0
        self._emit_interval = 0.07

    def update(self, dt, elapsed):
        cx, cy = config.FLOWER_CTR_X, config.FLOWER_CTR_Y

        if elapsed >= config.T_PARTICLES_ON:
            self._emit_timer += dt
            while self._emit_timer >= self._emit_interval:
                self._emit_timer -= self._emit_interval
                self._spawn(cx, cy)

        alive = []
        for p in self._particles:
            p.x  += p.vx * dt
            p.y  += p.vy * dt
            p.vy -= 10.0 * dt
            p.life -= dt
            if p.life > 0:
                alive.append(p)
        self._particles = alive

    def _spawn(self, cx, cy):
        rng = self._rng
        angle  = rng.uniform(0, 2 * math.pi)
        radius = rng.uniform(25, 170)
        x = cx + math.cos(angle) * radius
        y = cy + math.sin(angle) * radius
        speed  = rng.uniform(6, 28)
        vx = math.cos(angle) * speed * rng.uniform(0.25, 1.0)
        vy = math.sin(angle) * speed * rng.uniform(0.25, 1.0) - 18
        life = rng.uniform(0.9, 2.8)
        palette = [config.C_PARTICLE_A, config.C_PARTICLE_B, config.C_PARTICLE_C]
        color = palette[int(rng.integers(0, len(palette)))]
        self._particles.append(Particle(x, y, vx, vy, life, color))

    def get_render_data(self):
        out = []
        for p in self._particles:
            alpha = (p.life / p.max_life) ** 0.6
            r, g, b = p.color
            out.append((p.x, p.y, r*alpha, g*alpha, b*alpha))
        return out

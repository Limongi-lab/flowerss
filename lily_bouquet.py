"""Uma flor pra você: buquê de lírios animado (pygame + numpy).

Rodar:   python lily_bouquet.py
Sair:    ESC ou Q      |      Tela cheia: F11
"""
import math
import random
import time

import numpy as np
import pygame

# ----------------------------------------------------------------- config
W, H = 820, 920
FPS = 60
BASE_X, BASE_Y = 410, 790          # onde os caules se encontram
MESSAGE = "fiz pra você <3"
NAME = "com carinho, Rafael <3"

NST = 18                           # quantos estágios de abertura pré-renderizados
SS = 2                             # supersampling (bordas suaves)
BLOOM_DUR = 4.2                    # segundos que cada lírio leva pra abrir
T_MSG = 12.5                       # quando a mensagem aparece

# (escura, média, clara, garganta)
PALETTES = {
    "red":     ((150, 14, 28), (222, 40, 48), (255, 120, 105), (255, 205, 70)),
    "magenta": ((135, 26, 120), (212, 66, 182), (255, 155, 232), (255, 225, 125)),
    "white":   ((196, 184, 176), (238, 230, 222), (255, 251, 246), (255, 205, 95)),
    "cream":   ((214, 176, 136), (244, 214, 172), (255, 240, 212), (255, 170, 60)),
    "yellow":  ((205, 158, 14), (250, 214, 48), (255, 242, 135), (255, 140, 30)),
    "darkred": ((88, 8, 22), (146, 24, 44), (205, 72, 92), (255, 190, 70)),
    "pink":    ((196, 70, 132), (240, 140, 186), (255, 205, 228), (255, 222, 120)),
}

# x, y, raio, paleta, rotação, achatamento, atraso   (de trás pra frente)
LILIES = [
    (565, 285, 78, "yellow", 25, 0.88, 0.9),
    (385, 275, 82, "cream", -12, 0.90, 0.5),
    (452, 330, 112, "red", 12, 0.88, 0.0),
    (255, 450, 82, "yellow", -32, 0.85, 1.2),
    (590, 440, 98, "magenta", 24, 0.90, 0.7),
    (335, 400, 100, "white", -18, 0.87, 0.3),
    (610, 575, 88, "darkred", 32, 0.82, 1.4),
    (300, 545, 108, "pink", -8, 0.90, 1.0),
    (470, 515, 122, "white", 5, 0.85, 0.6),
    (395, 650, 88, "yellow", -4, 0.80, 1.6),
]

PETAL_ANGLES = [-90, 30, 150, -30, 90, 210]   # 3 de fora + 3 de dentro


# ---------------------------------------------------------------- helpers
def clamp(v, a=0.0, b=1.0):
    return max(a, min(b, v))


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_col(c1, c2, t):
    return tuple(int(lerp(c1[i], c2[i], t)) for i in range(3))


def smooth(t):
    t = clamp(t)
    return t * t * (3 - 2 * t)


def bezier(p0, p1, p2, p3, n):
    t = np.linspace(0.0, 1.0, n)[:, None]
    p0, p1, p2, p3 = (np.array(p, dtype=np.float64) for p in (p0, p1, p2, p3))
    return ((1 - t) ** 3) * p0 + 3 * ((1 - t) ** 2) * t * p1 + 3 * (1 - t) * t * t * p2 + t ** 3 * p3


# ------------------------------------------------------- render de 1 lírio
def petal_poly(L, Wd, t0, t1, wf, curl, n=14):
    ts = np.linspace(t0, t1, n)
    hw = Wd * wf * 2.6 * ts ** 0.6 * (1 - ts) ** 0.8
    off = curl * L * ts ** 2.5
    xs = ts * L
    left = np.stack([xs, -hw + off], 1)
    right = np.stack([xs, hw + off], 1)[::-1]
    return np.concatenate([left, right], 0)


def place(pts, ang, squash, cx, cy):
    a = math.radians(ang)
    c, s = math.cos(a), math.sin(a)
    x = pts[:, 0] * c - pts[:, 1] * s
    y = (pts[:, 0] * s + pts[:, 1] * c) * squash
    return [(cx + float(xx), cy + float(yy)) for xx, yy in zip(x, y)]


def render_lily(R, pal, rot, squash, b, seed):
    outer, mid, light, throat = pal
    S = int(R * 2.5)
    SB = S * SS
    surf = pygame.Surface((SB, SB), pygame.SRCALPHA)
    c = SB / 2
    e = smooth(b)
    spread = lerp(0.07, 1.0, e ** 0.8)
    Lmax = R * SS
    L0 = Lmax * lerp(0.5, 1.0, e ** 0.6)
    Wd = Lmax * 0.27 * lerp(0.5, 1.0, e)
    rng = random.Random(seed)
    vein_col = tuple(int(v * 0.65) for v in outer)
    spot_col = tuple(int(v * 0.55) for v in outer)

    for k, theta in enumerate(PETAL_ANGLES):
        inner = k >= 3
        d = ((theta + 90 + 180) % 360) - 180
        ang = -90 + d * spread + rot
        L = L0 * (0.95 if inner else 1.0)
        curl = (0.10 if k % 2 == 0 else -0.10) * e

        base = lerp_col(outer, mid, 0.55 if inner else 0.25)
        body = lerp_col(mid, light, 0.35) if inner else mid
        pygame.draw.polygon(surf, base, place(petal_poly(L, Wd, 0, 1, 1.0, curl), ang, squash, c, c))
        pygame.draw.polygon(surf, body, place(petal_poly(L, Wd, 0.04, 0.93, 0.66, curl), ang, squash, c, c))
        pygame.draw.polygon(surf, light, place(petal_poly(L, Wd, 0.10, 0.78, 0.22, curl), ang, squash, c, c))
        pygame.draw.polygon(surf, throat, place(petal_poly(L, Wd, 0.0, 0.30, 0.50, curl), ang, squash, c, c))

        ts = np.linspace(0.03, 0.88, 10)
        vein = np.stack([ts * L, curl * L * ts ** 2.5], 1)
        pygame.draw.lines(surf, vein_col, False, place(vein, ang, squash, c, c), max(1, int(SS * 1.2)))

        for _ in range(8):
            t = rng.uniform(0.14, 0.52)
            lat = rng.uniform(-0.5, 0.5) * (Wd * 2.6 * t ** 0.6 * (1 - t) ** 0.8)
            if e > 0.35:
                p = place(np.array([[t * L, lat + curl * L * t ** 2.5]]), ang, squash, c, c)[0]
                pygame.draw.circle(surf, spot_col, p, max(1, int(Lmax * 0.010)))

    if e > 0.4:
        Ls = Lmax * 0.5 * e
        for j in range(6):
            ang = -90 + (j - 2.5) * 24 * spread + rot
            tip_local = np.array([[0.0, 0.0], [Ls, Ls * 0.06 * (1 if j % 2 else -1)]])
            p0, p1 = place(tip_local, ang, squash, c, c)
            pygame.draw.line(surf, (240, 232, 190), p0, p1, max(1, SS))
            pygame.draw.circle(surf, (190, 82, 28), p1, max(2, int(Lmax * 0.032)))
        tip_local = np.array([[0.0, 0.0], [Lmax * 0.62 * e, 0.0]])
        p0, p1 = place(tip_local, -90 + 8 + rot, squash, c, c)
        pygame.draw.line(surf, (235, 240, 210), p0, p1, max(1, SS))
        pygame.draw.circle(surf, (255, 235, 235), p1, max(2, int(Lmax * 0.04)))

    surf = pygame.transform.smoothscale(surf, (S, S))

    # textura de linhas + "tracinhos" (efeito ASCII)
    nrng = np.random.default_rng(seed)
    arr = pygame.surfarray.pixels3d(surf)
    noise = nrng.uniform(0.80, 1.0, (S // 3 + 1, S))
    noise = np.repeat(noise, 3, axis=0)[:S]
    rows = np.ones(S)
    rows[::3] = 0.72
    arr[:] = (arr.astype(np.float32) * noise[:, :, None] * rows[None, :, None]).astype(np.uint8)
    del arr
    return surf


# ------------------------------------------------------------- componentes
class Lily:
    def __init__(self, spec, idx, rng):
        x, y, R, pal, rot, squash, delay = spec
        self.x, self.y, self.R = x, y, R
        self.pal = PALETTES[pal]
        self.rot, self.squash = rot, squash
        self.seed = 100 + idx
        self.stem_start = 0.4 + delay
        self.stem_dur = 3.6
        self.bloom_start = self.stem_start + self.stem_dur + 0.2
        self.phase = rng.uniform(0, 6.28)
        self.bx = BASE_X + rng.uniform(-38, 38)
        self.s1 = rng.uniform(-28, 28)
        self.s2 = rng.uniform(-28, 28)
        self.color = lerp_col((50, 140, 46), (110, 195, 70), rng.random())
        self.frames = []
        self.leaves = [(0.42, 1 if idx % 2 else -1), (0.68, -1 if idx % 2 else 1)]
        if y > 600:
            self.leaves = self.leaves[:1]

    def prerender(self):
        self.frames = [
            render_lily(self.R, self.pal, self.rot, self.squash, i / (NST - 1), self.seed)
            for i in range(NST)
        ]

    def stem(self, dx, dy):
        fx, fy = self.x + dx, self.y + dy
        p0 = (self.bx, BASE_Y)
        p1 = (self.bx + (fx - self.bx) * 0.1 + self.s1, BASE_Y - (BASE_Y - fy) * 0.40)
        p2 = (fx + self.s2, fy + (BASE_Y - fy) * 0.30)
        return bezier(p0, p1, p2, (fx, fy), 70)


class Blade:
    def __init__(self, rng):
        x = BASE_X + rng.uniform(-52, 52)
        tilt = rng.uniform(-0.95, 0.95)
        h = rng.uniform(110, 250)
        pts = bezier((x, BASE_Y), (x + tilt * h * 0.15, BASE_Y - h * 0.5),
                     (x + tilt * h * 0.6, BASE_Y - h * 0.85), (x + tilt * h * 0.95, BASE_Y - h), 26)
        tan = np.gradient(pts, axis=0)
        tan /= np.linalg.norm(tan, axis=1, keepdims=True) + 1e-9
        nor = np.stack([-tan[:, 1], tan[:, 0]], 1)
        s = np.linspace(0, 1, 26)
        w = (rng.uniform(5, 10) * (1 - s) ** 0.7 + 0.6)[:, None]
        self.left = (pts + nor * w).tolist()
        self.right = (pts - nor * w).tolist()
        self.n = 26
        self.start = 0.2 + rng.uniform(0, 2.6)
        self.dur = 3.4
        self.color = lerp_col((40, 120, 40), (120, 205, 70), rng.random())


class Sparkle:
    def __init__(self, rng, t0=0.0):
        self.rng = rng
        self.reset(t0)

    def reset(self, t0):
        r = self.rng
        a = r.uniform(0, 6.28)
        d = r.random() ** 0.6
        self.x = 410 + math.cos(a) * 210 * d
        self.y = 440 + math.sin(a) * 230 * d
        self.vx = r.uniform(-6, 6)
        self.vy = -r.uniform(8, 26)
        self.life = 0.0
        self.max = r.uniform(3.0, 6.0)
        self.col = r.choice([(255, 220, 235), (255, 235, 170), (255, 255, 255), (255, 170, 210)])
        self.size = r.choice([1, 1, 2])


def make_text(font, text, color, glow):
    base = font.render(text, True, color)
    pad = 14
    surf = pygame.Surface((base.get_width() + pad * 2, base.get_height() + pad * 2), pygame.SRCALPHA)
    g = font.render(text, True, glow)
    g.set_alpha(70)
    for ox, oy in [(-3, 0), (3, 0), (0, -3), (0, 3), (-2, -2), (2, -2), (-2, 2), (2, 2), (-5, 0), (5, 0), (0, 5), (0, -5)]:
        surf.blit(g, (pad + ox, pad + oy))
    surf.blit(base, (pad, pad))
    return surf


# -------------------------------------------------------------------- app
class Bouquet:
    def __init__(self, screen):
        self.screen = screen
        rng = random.Random(7)
        self.lilies = [Lily(spec, i, rng) for i, spec in enumerate(LILIES)]
        self.blades = [Blade(rng) for _ in range(20)]
        self.stars = [(rng.randrange(W), rng.randrange(H), rng.randint(50, 150), rng.uniform(0, 6.28), rng.choice([1, 1, 2]))
                      for _ in range(150)]
        self.sparkles = [Sparkle(rng) for _ in range(55)]
        for sp in self.sparkles:
            sp.life = rng.uniform(0, sp.max)
        self._last_t = 0.0

        # brilho suave atrás do buquê
        gw, gh = 620, 700
        yy, xx = np.mgrid[0:gh, 0:gw]
        dist = ((xx - gw / 2) / (gw / 2)) ** 2 + ((yy - gh / 2) / (gh / 2)) ** 2
        alpha = (np.exp(-dist * 2.6) * 95).astype(np.uint8)
        self.glow = pygame.Surface((gw, gh), pygame.SRCALPHA)
        self.glow.fill((255, 95, 150, 255))
        pygame.surfarray.pixels_alpha(self.glow)[:] = alpha.T

        # linhas de varredura sobre tudo
        self.scan = pygame.Surface((W, H), pygame.SRCALPHA)
        for y in range(2, H, 3):
            pygame.draw.line(self.scan, (0, 0, 0, 55), (0, y), (W, y))

        fonts = "georgia,cambria,palatinolinotype,timesnewroman,serif"
        self.msg = make_text(pygame.font.SysFont(fonts, 46, italic=True), MESSAGE, (255, 228, 238), (255, 120, 175))
        self.name = make_text(pygame.font.SysFont(fonts, 28, italic=True), NAME, (255, 175, 205), (255, 110, 160))

        # pré-renderiza todos os lírios (acontece uma vez, na abertura)
        for lily in self.lilies:
            lily.prerender()
            pygame.event.pump()

    # ------------------------------------------------------------ desenho
    def draw(self, t):
        scr = self.screen
        dt = clamp(t - self._last_t, 0.0, 0.1)
        self._last_t = t
        scr.fill((0, 0, 0))

        # estrelinhas
        sf = smooth(t / 3.0)
        for x, y, br, ph, sz in self.stars:
            v = int(br * (0.65 + 0.35 * math.sin(t * 1.3 + ph)) * sf)
            scr.fill((v, v, min(255, int(v * 1.15))), (x, y, sz, sz))

        # brilho
        g = smooth((t - 4.5) / 7.0) * 0.85
        if t > 12:
            g += 0.07 * math.sin((t - 12) * 1.1)
        if g > 0.01:
            self.glow.set_alpha(int(255 * clamp(g)))
            scr.blit(self.glow, (BASE_X - 310, 450 - 350))

        sway = smooth((t - 6.0) / 4.0)

        # caules + folhas
        for lily in self.lilies:
            frac = smooth((t - lily.stem_start) / lily.stem_dur)
            if frac <= 0:
                continue
            dx = sway * 3.0 * math.sin(1.0 * t + lily.phase)
            dy = sway * 1.5 * math.sin(1.4 * t + lily.phase * 1.3)
            pts = lily.stem(dx, dy)
            k = max(2, int(frac * (len(pts) - 1)) + 1)
            line = pts[:k].tolist()
            pygame.draw.lines(scr, lily.color, False, line, 3)
            pygame.draw.lines(scr, lerp_col(lily.color, (230, 255, 190), 0.35), False,
                              [(px - 1, py) for px, py in line], 1)
            for pos, side in lily.leaves:
                idx = int(pos * (len(pts) - 1))
                grow = clamp((frac * (len(pts) - 1) - idx) / 12.0)
                if grow > 0:
                    self._leaf(pts, idx, side, grow, lily.color)

        # tufo de folhas na base
        for bl in self.blades:
            f = smooth((t - bl.start) / bl.dur)
            k = int(f * (bl.n - 1)) + 1
            if k >= 3:
                pygame.draw.polygon(scr, bl.color, bl.left[:k] + bl.right[:k][::-1])

        # lírios
        for lily in self.lilies:
            frac = (t - lily.stem_start) / lily.stem_dur
            if frac < 1.0:
                continue
            dx = sway * 3.0 * math.sin(1.0 * t + lily.phase)
            dy = sway * 1.5 * math.sin(1.4 * t + lily.phase * 1.3)
            cx, cy = lily.x + dx, lily.y + dy
            b = smooth((t - lily.bloom_start) / BLOOM_DUR)
            pos = b * (NST - 1)
            i0 = int(pos)
            i1 = min(NST - 1, i0 + 1)
            f = pos - i0
            appear = clamp((t - (lily.stem_start + lily.stem_dur)) / 0.6)
            s0 = lily.frames[i0]
            s0.set_alpha(int(255 * appear))
            scr.blit(s0, s0.get_rect(center=(cx, cy)))
            if f > 0.01 and i1 != i0:
                s1 = lily.frames[i1]
                s1.set_alpha(int(255 * f))
                scr.blit(s1, s1.get_rect(center=(cx, cy)))

        # brilhinhos subindo
        if t > 7.0:
            fade_in = smooth((t - 7.0) / 3.0)
            for sp in self.sparkles:
                sp.life += dt
                if sp.life > sp.max:
                    sp.reset(t)
                sp.x += sp.vx * dt + math.sin(t + sp.max) * 4 * dt
                sp.y += sp.vy * dt
                a = math.sin(math.pi * sp.life / sp.max) * fade_in
                col = tuple(int(c * a) for c in sp.col)
                if sp.size == 1:
                    scr.fill(col, (int(sp.x), int(sp.y), 2, 2))
                else:
                    pygame.draw.circle(scr, col, (int(sp.x), int(sp.y)), 2)

        scr.blit(self.scan, (0, 0))

        # textos
        a = smooth((t - T_MSG) / 2.0)
        if a > 0:
            self.msg.set_alpha(int(255 * a))
            scr.blit(self.msg, self.msg.get_rect(center=(W // 2, H - 80)))
        a2 = smooth((t - T_MSG - 1.5) / 2.0)
        if a2 > 0:
            self.name.set_alpha(int(210 * a2))
            scr.blit(self.name, self.name.get_rect(bottomright=(W - 14, H - 10)))

    def _leaf(self, pts, idx, side, grow, color):
        i0, i1 = max(0, idx - 1), min(len(pts) - 1, idx + 1)
        tx, ty = pts[i1][0] - pts[i0][0], pts[i1][1] - pts[i0][1]
        ang = math.atan2(ty, tx) + side * math.radians(58)
        dx, dy = math.cos(ang), math.sin(ang)
        nx, ny = -dy, dx
        px, py = pts[idx]
        Lf = 90 * grow
        hw = 10 * grow
        up, dn, mid = [], [], []
        for j in range(11):
            s = j / 10
            w = hw * math.sin(math.pi * s) ** 0.7
            cx = px + dx * Lf * s
            cy = py + dy * Lf * s + 0.14 * Lf * s * s
            up.append((cx + nx * w, cy + ny * w))
            dn.append((cx - nx * w, cy - ny * w))
            mid.append((cx, cy))
        pygame.draw.polygon(self.screen, lerp_col(color, (30, 100, 35), 0.35), up + dn[::-1])
        pygame.draw.lines(self.screen, lerp_col(color, (230, 255, 190), 0.4), False, mid, 1)


def main():
    pygame.init()
    pygame.display.set_caption("Uma flor pra você")
    screen = pygame.display.set_mode((W, H), pygame.SCALED)

    # tela de espera enquanto os lírios são preparados
    screen.fill((0, 0, 0))
    wait = pygame.font.SysFont("georgia,serif", 30, italic=True).render("preparando...", True, (200, 120, 160))
    screen.blit(wait, wait.get_rect(center=(W // 2, H // 2)))
    pygame.display.flip()

    app = Bouquet(screen)
    clock = pygame.time.Clock()
    start = time.perf_counter()
    running = True
    while running:
        for ev in pygame.event.get():
            if ev.type == pygame.QUIT:
                running = False
            elif ev.type == pygame.KEYDOWN:
                if ev.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                elif ev.key == pygame.K_F11:
                    pygame.display.toggle_fullscreen()
        app.draw(time.perf_counter() - start)
        pygame.display.flip()
        clock.tick(FPS)
    pygame.quit()


if __name__ == "__main__":
    main()

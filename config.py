# ============================================================
#  config.py  –  A Flower For You
#  All tuneable constants in one place.
# ============================================================

# ── Window ───────────────────────────────────────────────────
WIDTH  = 700
HEIGHT = 800
TITLE  = "A Flower For You"
BG_HEX = "#030305"   # very near-black

# Target frame rate
FPS = 30

# ── Flower layout (pixels) ──────────────────────────────────
STEM_BASE_X  = 350
STEM_BASE_Y  = 790
FLOWER_CTR_X = 350
FLOWER_CTR_Y = 310

# ── Animation phase timing (seconds) ────────────────────────
T_STEM_START      = 0.0
T_STEM_END        = 4.5

T_LEAVES_START    = 1.5
T_LEAVES_END      = 6.5

T_BUD_START       = 4.0
T_BUD_END         = 8.0

T_BLOOM_START     = 7.0
T_BLOOM_END       = 15.0

T_STAMENS_START   = 11.0
T_STAMENS_END     = 13.5

T_PARTICLES_ON    = 9.0

T_MSG_FADE_START  = 15.5
T_MSG_FADE_END    = 18.0

T_TOTAL           = 22.0   # animation "complete" after this

# ── Dot style ───────────────────────────────────────────────
DOT_JITTER   = 1.0    # px; Gaussian position noise
DOT_SPACING  = 2.2    # average spacing when sampling paths

# ── Sizes ───────────────────────────────────────────────────
STEM_LENGTH   = 490   # px: base → flower centre
PETAL_LENGTH  = 175   # px: long, elegant lily petals
PETAL_MAX_W   =  38   # px: narrower half-width (more lily-like)
LEAF_LENGTH   =  95   # px
BUD_LENGTH    = 110   # px
BUD_MAX_W     =  14   # px half-width

# ── Colour palette (RGB, 0-1 float) ─────────────────────────

# Stem / leaves
C_STEM_CORE  = (0.04, 0.38, 0.20)
C_STEM_GLOW  = (0.00, 0.65, 0.35)
C_LEAF_CORE  = (0.03, 0.44, 0.19)
C_LEAF_GLOW  = (0.08, 0.68, 0.30)

# Petals – inner → outer gradient
C_PET_INNER  = (1.00, 0.55, 0.80)   # bright pinkish-white
C_PET_MID    = (0.90, 0.10, 0.50)   # hot magenta
C_PET_OUTER  = (0.65, 0.01, 0.30)   # deep magenta
C_PET_EDGE   = (0.18, 0.08, 0.92)   # blue-violet edge highlight

# Bud
C_BUD_INNER  = (0.80, 0.30, 0.65)
C_BUD_OUTER  = (0.48, 0.00, 0.28)

# Stamens / anthers
C_STAMEN  = (0.90, 0.78, 0.22)
C_ANTHER  = (1.00, 0.95, 0.40)

# Pistil (centre cluster)
C_CENTER  = (1.00, 0.70, 0.90)

# Sparkle particles
C_PARTICLE_A = (1.00, 0.70, 0.88)   # soft pink
C_PARTICLE_B = (0.55, 0.78, 1.00)   # ice blue
C_PARTICLE_C = (1.00, 0.98, 0.88)   # near-white warm

# Message
C_MESSAGE         = (0.78, 0.60, 0.80)   # lavender-grey
MESSAGE_TEXT      = "Made this little flower for you."
MESSAGE_FONT_SIZE = 19

# ── Post-process glow ────────────────────────────────────────
GLOW_BLUR_RADIUS = 5     # PIL GaussianBlur radius
GLOW_STRENGTH    = 0.60  # how strongly the blurred layer is blended back

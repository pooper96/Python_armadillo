# ui/constants.py
# Visual tokens, timings, and shared helpers for the Armadillo game UI.
from kivy.metrics import dp, sp

# ---- Colors (RGBA 0..1) ----
BG          = (0.10, 0.12, 0.15, 1)
CARD        = (0.18, 0.20, 0.24, 1)
CARD_ALT    = (0.20, 0.22, 0.27, 1)
SURFACE     = (0.14, 0.16, 0.19, 1)
ACCENT      = (0.22, 0.78, 0.55, 1)
ACCENT_DIM  = (0.22, 0.78, 0.55, .2)
WARNING     = (0.95, 0.75, 0.18, 1)
DANGER      = (0.92, 0.31, 0.31, 1)
INFO        = (0.33, 0.65, 0.98, 1)
TEXT        = (0.95, 0.97, 1.00, 1)
TEXT_DIM    = (0.85, 0.87, 0.92, 1)
BORDER      = (1, 1, 1, .06)
SUCCESS     = (0.21, 0.72, 0.44, 1)
HOVER       = (1, 1, 1, .05)

# ---- Radii, elevation ----
R           = dp(14)
R_SMALL     = dp(10)
R_LARGE     = dp(20)
ELEVATION_1 = (.18, .24)  # (shadow alpha near, far) for a two-layer fake shadow

# ---- Typography (sp) ----
H1  = sp(22)
H2  = sp(18)
BODY= sp(15)
SMALL=sp(13)

# ---- Touch & Motion ----
LONG_PRESS_MS      = 350
DRAG_GHOST_SCALE   = 1.05
DRAG_SNAP_MS       = 120
TOAST_SECS         = 2.0

# ---- Layout ----
TOPBAR_H   = dp(48)
BOTNAV_H   = dp(64)
SAFE_TOP   = dp(24)   # conservative status bar inset; adjusted at runtime when possible
SAFE_BOT   = dp(16)

# ---- Z orders (Canvas instructions sort via instructions order; use for reference) ----
Z_TOAST    = 1000
Z_DIALOG   = 1100
Z_DRAG     = 1200

# ---- Utility stubs ----
def tr(s: str) -> str:
    """Localization placeholder; route all user-visible strings through tr()."""
    return s

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

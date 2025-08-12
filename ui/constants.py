from kivy.metrics import dp, sp

BG          = (0.10, 0.12, 0.15, 1)
CARD        = (0.18, 0.20, 0.24, 1)
ACCENT      = (0.22, 0.78, 0.55, 1)
WARNING     = (0.95, 0.75, 0.18, 1)
DANGER      = (0.92, 0.31, 0.31, 1)
TEXT        = (0.95, 0.97, 1.00, 1)
TEXT_DIM    = (0.85, 0.87, 0.92, 1)
BORDER      = (1, 1, 1, .06)

R           = dp(14)
TOPBAR_H    = dp(48)
BOTNAV_H    = dp(64)

H1  = sp(22)
H2  = sp(18)
BODY= sp(15)
SMALL=sp(13)

LONG_PRESS_MS    = 350
DRAG_GHOST_SCALE = 1.05
TOAST_SECS       = 2.0

def tr(s: str) -> str:
    return s

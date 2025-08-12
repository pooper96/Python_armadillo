from __future__ import annotations
from typing import List, Tuple, Dict
from kivy.graphics.texture import Texture
from settings import Settings


def _to_rgba_bytes(r: float, g: float, b: float, a: float = 1.0) -> bytes:
    return bytes([int(max(0, min(1, r)) * 255),
                  int(max(0, min(1, g)) * 255),
                  int(max(0, min(1, b)) * 255),
                  int(max(0, min(1, a)) * 255)])


def _tint(base: Tuple[float, float, float], tint_rgb: Tuple[float, float, float]) -> Tuple[float, float, float]:
    # simple multiply tint (keeps pixel-art palette feel)
    return (base[0] * tint_rgb[0], base[1] * tint_rgb[1], base[2] * tint_rgb[2])


class ProceduralAssets:
    """
    Builds tiny 16x12 pixel sprites for armadillos and returns Kivy Textures.
    Two frames = simple waddle. We scale them with mag_filter='nearest' for crisp pixels.
    """
    def __init__(self, settings: Settings):
        self.settings = settings
        self._cache: Dict[Tuple[Tuple[float, float, float], int], Texture] = {}

    def armadillo_frames(self, rgb: Tuple[float, float, float]) -> List[Texture]:
        # Two frames keyed by frame index
        return [self._get_frame(rgb, 0), self._get_frame(rgb, 1)]

    # ---- internals ----
    def _get_frame(self, rgb: Tuple[float, float, float], frame: int) -> Texture:
        key = (rgb, frame)
        if key in self._cache:
            return self._cache[key]

        w, h = 16, 12
        buf = bytearray(w * h * 4)

        sand = (0.82, 0.74, 0.57)
        shell = _tint((0.7, 0.62, 0.5), rgb)
        head = _tint((0.8, 0.7, 0.55), rgb)
        leg = _tint((0.55, 0.48, 0.38), rgb)
        eye = (0.1, 0.1, 0.1)

        def put(px, py, color):
            if 0 <= px < w and 0 <= py < h:
                i = (py * w + px) * 4
                rb = _to_rgba_bytes(*color)
                buf[i:i+4] = rb

        # clear transparent
        for i in range(0, len(buf), 4):
            buf[i:i+4] = _to_rgba_bytes(0, 0, 0, 0)

        # very simple side view (12x6 body)
        # body (shell plates as 3 stripes)
        for y in range(4, 9):
            for x in range(2, 13):
                c = shell
                if y in (5, 7, 8):  # darker strips
                    c = _tint((0.85, 0.85, 0.85), shell)
                put(x, y, c)

        # head
        for y in range(5, 8):
            for x in range(12, 15):
                put(x, y, head)
        put(14, 7, eye)

        # legs (alternate frame offsets)
        leg_y = 3 if frame == 0 else 4
        for x in (4, 9):
            put(x, leg_y, leg)
        leg_y2 = 4 if frame == 0 else 3
        for x in (6, 11):
            put(x, leg_y2, leg)

        # convert to texture
        tex = Texture.create(size=(w, h))
        tex.blit_buffer(bytes(buf), colorfmt='rgba', bufferfmt='ubyte')
        tex.wrap = 'clamp_to_edge'
        tex.min_filter = 'nearest'
        tex.mag_filter = 'nearest'
        self._cache[key] = tex
        return tex

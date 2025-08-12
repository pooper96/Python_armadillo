from __future__ import annotations
from typing import List, Tuple, Dict
from kivy.graphics.texture import Texture


def _clamp01(x: float) -> float:
    return 0 if x < 0 else 1 if x > 1 else x


def _rgba(r, g, b, a=1.0) -> bytes:
    return bytes([int(_clamp01(r) * 255),
                  int(_clamp01(g) * 255),
                  int(_clamp01(b) * 255),
                  int(_clamp01(a) * 255)])


def _mul(c: Tuple[float, float, float], t: Tuple[float, float, float]):
    return (c[0]*t[0], c[1]*t[1], c[2]*t[2])


class ProceduralAssets:
    """
    Generates 24x16 pixel-art armadillo sprites in 4 frames (walk cycle).
    Textures are scaled with nearest-neighbor for crisp pixels.
    """
    def __init__(self, settings):
        self.settings = settings
        self._cache: Dict[Tuple[Tuple[float,float,float], int], Texture] = {}

    # public
    def armadillo_frames(self, rgb: Tuple[float, float, float]) -> List[Texture]:
        return [self._frame(rgb, i) for i in range(4)]

    # internals
    def _frame(self, rgb, idx) -> Texture:
        key = (rgb, idx)
        if key in self._cache:
            return self._cache[key]

        w, h = 24, 16
        buf = bytearray(w * h * 4)

        def put(px, py, col):
            if 0 <= px < w and 0 <= py < h:
                i = (py * w + px) * 4
                buf[i:i+4] = _rgba(*col)

        # clear transparent
        trans = _rgba(0, 0, 0, 0)
        for i in range(0, len(buf), 4):
            buf[i:i+4] = trans

        # palette
        shell = _mul((0.72, 0.64, 0.52), rgb)
        shell_dark = _mul((0.60, 0.54, 0.44), rgb)
        head = _mul((0.86, 0.78, 0.62), rgb)
        leg = _mul((0.40, 0.35, 0.28), rgb)
        ear = head
        tail = shell_dark
        eye = (0.08, 0.08, 0.08)

        # body shell (rounded rectangle)
        for y in range(6, 13):
            for x in range(3, 18):
                # carve rounded top
                if y == 6 and x in (3, 17):
                    continue
                put(x, y, shell)
        # bands
        for y in (7, 9, 11):
            for x in range(4, 17):
                put(x, y, shell_dark)

        # head + snout
        for y in range(7, 12):
            for x in range(17, 22):
                put(x, y, head)
        for x in range(22, 24):
            put(x, 9, head)
        put(21, 10, eye)
        # ear
        put(20, 12, ear)

        # tail
        for y in (8, 9, 10):
            put(2, y, tail)

        # legs – alternate by frame: 0/2 vs 1/3
        low = 4 if idx % 2 == 0 else 5
        hi = 5 if idx % 2 == 0 else 4
        for x in (5, 9):  # front pair
            put(x, low, leg)
        for x in (12, 15):  # back pair
            put(x, hi, leg)

        # convert to texture
        tex = Texture.create(size=(w, h))
        tex.blit_buffer(bytes(buf), colorfmt='rgba', bufferfmt='ubyte')
        tex.wrap = 'clamp_to_edge'
        tex.min_filter = 'nearest'
        tex.mag_filter = 'nearest'
        self._cache[key] = tex
        return tex

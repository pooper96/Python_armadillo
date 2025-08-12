# ui/drag.py
# Long-press drag manager + drop zones.
from kivy.clock import Clock
from kivy.properties import (BooleanProperty, ListProperty, ObjectProperty, NumericProperty)
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, RoundedRectangle
from kivy.core.window import Window

from .constants import (LONG_PRESS_MS, DRAG_GHOST_SCALE, R, ACCENT, DANGER, HOVER)

class DropZoneMixin(Widget):
    accept_types = ListProperty(["armadillo"])
    is_hovered = BooleanProperty(False)
    highlight_color = ListProperty([*HOVER])

    def accepts(self, payload: dict) -> bool:
        """Override for stricter logic. Default accepts by type."""
        return payload and payload.get("type") in self.accept_types

    def on_drop(self, payload: dict):
        """Override to mutate game state."""
        pass

    def on_is_hovered(self, *_):
        self.canvas.ask_update()

    def on_kv_post(self, *a):
        with self.canvas.before:
            self._hover_col = Color(*self.highlight_color)
            self._hover_bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[R]*4)
        self.bind(pos=self._sync, size=self._sync, highlight_color=self._sync, is_hovered=self._update_hover)
        self._update_hover()

    def _sync(self, *_):
        self._hover_bg.pos = self.pos
        self._hover_bg.size = self.size

    def _update_hover(self, *_):
        self._hover_col.rgba = (self.highlight_color if self.is_hovered else (0,0,0,0))

class DragProxy(Widget):
    payload = ObjectProperty(allownone=True)
    scale = NumericProperty(DRAG_GHOST_SCALE)

class DragManager(FloatLayout):
    instance = None

    def __init__(self, **kw):
        super().__init__(**kw)
        self._active = False
        self._source = None
        self._proxy = None
        self._payload = None
        self._lp_ev = None
        self._hovered_zone = None
        Window.bind(on_touch_down=self._down, on_touch_up=self._up, on_touch_move=self._move)

    @classmethod
    def attach(cls, root):
        if cls.instance is None:
            cls.instance = DragManager()
            root.add_widget(cls.instance)

    def _down(self, win, touch):
        if touch.is_mouse_scrolling:
            return
        if len(win.touches) > 1:
            # cancel any pending
            self._cancel()
            return
        # schedule long-press
        self._source = touch.ud.get('widget', touch.widget)
        self._lp_ev = Clock.schedule_once(lambda dt: self._start(touch), LONG_PRESS_MS / 1000.0)
        touch.ud['lp_scheduled'] = True

    def _start(self, touch):
        if not touch.ud.get('lp_scheduled'):
            return
        self._active = True
        # Build payload from source if possible
        srcw = touch.widget
        payload = getattr(srcw, 'drag_payload', None)
        if callable(payload):
            payload = payload()
        self._payload = payload or {"type": "unknown"}
        # Proxy: simple rounded rect; avoid textures for perf
        self._proxy = DragProxy(payload=self._payload, size=(touch.widget.width*1.05, touch.widget.height*1.05))
        with self._proxy.canvas:
            Color(1, 1, 1, .08)
            self._proxy._bg = RoundedRectangle(pos=(touch.x - self._proxy.width/2, touch.y - self._proxy.height/2),
                                               size=self._proxy.size, radius=[R]*4)
        self.add_widget(self._proxy)
        self._move(Window, touch)

    def _move(self, win, touch):
        if not self._active or not self._proxy:
            return
        self._proxy._bg.pos = (touch.x - self._proxy.width/2, touch.y - self._proxy.height/2)
        # Hover detection
        hovered = None
        for w in self.walk_reverse(loopback=False):
            if isinstance(w, DropZoneMixin) and w.collide_point(*touch.pos):
                hovered = w
                break
        if self._hovered_zone and self._hovered_zone is not hovered:
            self._hovered_zone.is_hovered = False
        self._hovered_zone = hovered
        if hovered:
            ok = hovered.accepts(self._payload)
            hovered.is_hovered = True
            color = ACCENT if ok else DANGER
            hovered.highlight_color = (*color[:3], .12)

    def _up(self, win, touch):
        if self._lp_ev:
            self._lp_ev.cancel()
            self._lp_ev = None
        if not self._active:
            return
        # Drop
        if self._hovered_zone and self._hovered_zone.accepts(self._payload):
            self._hovered_zone.on_drop(self._payload)
        # cleanup
        self._cancel()

    def _cancel(self):
        self._active = False
        self._source = None
        self._payload = None
        if self._hovered_zone:
            self._hovered_zone.is_hovered = False
            self._hovered_zone = None
        if self._proxy:
            self.remove_widget(self._proxy)
            self._proxy = None

from kivy.clock import Clock
from kivy.properties import BooleanProperty, ListProperty, ObjectProperty, NumericProperty
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, RoundedRectangle
from kivy.app import App

from .constants import LONG_PRESS_MS, DRAG_GHOST_SCALE, R, ACCENT, DANGER


class DropZoneMixin(Widget):
    """Mixin for widgets that can receive a drop."""
    accept_types = ListProperty(["armadillo"])
    is_hovered = BooleanProperty(False)
    highlight_color = ListProperty([0, 0, 0, 0])

    def accepts(self, payload: dict) -> bool:
        return payload and payload.get("type") in self.accept_types

    def on_drop(self, payload: dict):
        """Override in subclasses."""
        pass

    def on_kv_post(self, *a):
        with self.canvas.before:
            self._col = Color(*self.highlight_color)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[R] * 4)
        self.bind(pos=self._sync, size=self._sync,
                  highlight_color=self._apply_hover, is_hovered=self._apply_hover)
        self._apply_hover()

    def _sync(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size

    def _apply_hover(self, *_):
        self._col.rgba = self.highlight_color if self.is_hovered else (0, 0, 0, 0)


class DragProxy(Widget):
    payload = ObjectProperty(allownone=True)
    scale = NumericProperty(DRAG_GHOST_SCALE)


class DragManager(FloatLayout):
    """Top-level overlay that manages long-press drag & drop.

    - Long-press start (350ms) before dragging
    - Cancels if a second finger touches
    - Creates a simple ghost rectangle
    - Highlights hovered DropZones (green/red)
    """
    instance = None

    def __init__(self, **kw):
        super().__init__(**kw)
        self._active = False
        self._proxy = None
        self._payload = None
        self._lp_ev = None
        self._hovered_zone = None
        self._touch_ids = set()  # track active touches (Window.touches is not available)

        from kivy.core.window import Window
        Window.bind(on_touch_down=self._down,
                    on_touch_up=self._up,
                    on_touch_move=self._move)

    @classmethod
    def attach(cls, root):
        """Attach a singleton overlay to the given root widget."""
        if cls.instance is None:
            cls.instance = DragManager()
            root.add_widget(cls.instance)

    # ---------------- internal helpers ----------------

    def _find_draggable_under(self, pos):
        """Return the topmost widget under 'pos' that exposes drag_payload()."""
        app = App.get_running_app()
        if not app or not app.root:
            return None
        for w in app.root.walk_reverse(loopback=False):
            if hasattr(w, "drag_payload") and callable(getattr(w, "drag_payload")):
                try:
                    if w.collide_point(*pos):
                        return w
                except Exception:
                    pass
        return None

    def _find_dropzone_under(self, pos):
        app = App.get_running_app()
        if not app or not app.root:
            return None
        for w in app.root.walk_reverse(loopback=False):
            if isinstance(w, DropZoneMixin):
                try:
                    if w.collide_point(*pos):
                        return w
                except Exception:
                    pass
        return None

    def _cancel(self):
        self._active = False
        if self._hovered_zone:
            self._hovered_zone.is_hovered = False
            self._hovered_zone = None
        if self._proxy:
            self.remove_widget(self._proxy)
            self._proxy = None
        self._payload = None
        if self._lp_ev:
            self._lp_ev.cancel()
            self._lp_ev = None

    # ---------------- Window event handlers ----------------

    def _down(self, win, touch):
        if getattr(touch, "is_mouse_scrolling", False):
            return
        self._touch_ids.add(touch.uid)

        # Cancel any pending/active drag on multi-touch
        if len(self._touch_ids) > 1:
            self._cancel()
            return

        # Schedule long-press start
        touch.ud["lp_scheduled"] = True
        self._lp_ev = Clock.schedule_once(lambda dt: self._start(touch),
                                          LONG_PRESS_MS / 1000.0)

    def _start(self, touch):
        if not touch.ud.get("lp_scheduled"):
            return

        srcw = self._find_draggable_under(touch.pos)
        if srcw is None:
            self._cancel()
            return

        # Build payload and proxy
        payload = srcw.drag_payload()
        if not payload:
            self._cancel()
            return

        self._active = True
        self._payload = payload

        self._proxy = DragProxy(payload=payload,
                                size=(srcw.width * DRAG_GHOST_SCALE,
                                      srcw.height * DRAG_GHOST_SCALE))
        with self._proxy.canvas:
            Color(1, 1, 1, 0.08)
            self._proxy._bg = RoundedRectangle(
                pos=(touch.x - self._proxy.width / 2, touch.y - self._proxy.height / 2),
                size=self._proxy.size,
                radius=[R] * 4,
            )
        self.add_widget(self._proxy)
        self._move(None, touch)

    def _move(self, win, touch):
        # Multi-touch during long-press cancels the pending start
        if self._lp_ev and touch.ud.get("lp_scheduled") and len(self._touch_ids) > 1:
            self._cancel()
            return

        if not self._active or not self._proxy:
            return

        # Move ghost
        self._proxy._bg.pos = (touch.x - self._proxy.width / 2,
                               touch.y - self._proxy.height / 2)

        # Highlight hovered zone
        hovered = self._find_dropzone_under(touch.pos)
        if self._hovered_zone and self._hovered_zone is not hovered:
            self._hovered_zone.is_hovered = False
        self._hovered_zone = hovered

        if hovered:
            ok = hovered.accepts(self._payload)
            hovered.is_hovered = True
            hovered.highlight_color = (
                ACCENT[0], ACCENT[1], ACCENT[2], 0.12
            ) if ok else (
                DANGER[0], DANGER[1], DANGER[2], 0.12
            )

    def _up(self, win, touch):
        self._touch_ids.discard(touch.uid)

        if self._lp_ev:
            # If we release before the long-press fired, just cancel cleanly
            self._lp_ev.cancel()
            self._lp_ev = None
            touch.ud["lp_scheduled"] = False

        if not self._active:
            return

        if self._hovered_zone and self._hovered_zone.accepts(self._payload):
            try:
                self._hovered_zone.on_drop(self._payload)
            except Exception:
                pass
        self._cancel()

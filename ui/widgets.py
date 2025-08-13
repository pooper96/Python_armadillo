from functools import partial
from kivy.clock import Clock
from kivy.properties import (
    StringProperty,
    NumericProperty,
    ListProperty,
    BooleanProperty,
    ObjectProperty,
)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.modalview import ModalView
from kivy.animation import Animation
from kivy.graphics import Color, RoundedRectangle, Rectangle
from kivy.app import App  # correct API for running app

from .constants import (
    BG,
    CARD,
    TEXT,
    TEXT_DIM,
    ACCENT,
    BORDER,
    R,
    H1,
    H2,
    BODY,
    SMALL,
    TOAST_SECS,
    TOPBAR_H,
    BOTNAV_H,
    tr,
)


def log_event(name: str, **kwargs):  # analytics stub
    pass


class Haptics:
    enabled = True

    @classmethod
    def tap(cls):
        if cls.enabled:
            log_event("haptic_tap")


class ALabel(Label):
    """Accessible label that respects 'large text' setting."""
    base_size = NumericProperty(BODY)

    def on_kv_post(self, *a):
        self.bind(base_size=self._apply)
        self._apply()

    def _apply(self, *a):
        app = App.get_running_app()
        mult = 1.15 if (app and getattr(app, "large_text", False)) else 1.0
        self.font_size = self.base_size * mult


class Counter(ALabel):
    value = NumericProperty(0)
    duration = NumericProperty(0.3)
    fmt = StringProperty("{:,.0f}")

    def set_value(self, new_val: float):
        Animation(value=new_val, duration=self.duration, t="out_quad").start(self)

    def on_value(self, *_):
        self.text = self.fmt.format(self.value)


class TopBar(BoxLayout):
    title = StringProperty("Armadillo")
    coins = NumericProperty(0)
    on_settings = ObjectProperty(lambda *_: None)

    def __init__(self, **kw):
        super().__init__(**kw)
        self.height = TOPBAR_H
        self.size_hint_y = None
        with self.canvas.before:
            Color(*BG)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._sync_bg, size=self._sync_bg)

    def _sync_bg(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size

    def increment_coins(self, delta: int):
        self.coins += delta
        Haptics.tap()
        ToastManager.show(tr(f"+{delta} coins"))
        log_event("coins_changed", delta=delta)


class NavButton(ButtonBehavior, BoxLayout):
    tab = StringProperty("")
    label = StringProperty("")
    active = BooleanProperty(False)
    icon = StringProperty("")


class BottomNav(BoxLayout):
    current = StringProperty("home")
    on_tab = ObjectProperty(lambda tab: None)

    def __init__(self, **kw):
        super().__init__(**kw)
        self.size_hint_y = None
        self.height = BOTNAV_H
        with self.canvas.before:
            Color(*BG)
            self._bg = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._sync_bg, size=self._sync_bg)

    def _sync_bg(self, *_):
        self._bg.pos = self.pos
        self._bg.size = self.size


class Card(BoxLayout):
    elevated = BooleanProperty(True)

    def __init__(self, **kw):
        super().__init__(**kw)
        with self.canvas.before:
            if self.elevated:
                Color(0, 0, 0, 0.18)
                self._sh1 = RoundedRectangle(
                    pos=(self.x, self.y - 2), size=self.size, radius=[R] * 4
                )
                Color(0, 0, 0, 0.10)
                self._sh2 = RoundedRectangle(
                    pos=(self.x, self.y - 1), size=self.size, radius=[R] * 4
                )
            Color(*CARD)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[R] * 4)
        self.bind(pos=self._sync_bg, size=self._sync_bg)

    def _sync_bg(self, *_):
        if hasattr(self, "_sh1"):
            self._sh1.pos = (self.x, self.y - 2)
            self._sh1.size = self.size
            self._sh2.pos = (self.x, self.y - 1)
            self._sh2.size = self.size
        self._bg.pos = self.pos
        self._bg.size = self.size


class SmoothProgress(Widget):
    value = NumericProperty(0.0)
    display = NumericProperty(0.0)
    speed = NumericProperty(6.0)

    def __init__(self, **kw):
        super().__init__(**kw)
        with self.canvas:
            Color(*ACCENT)
            self._fg = Rectangle(pos=self.pos, size=(0, self.height))
        with self.canvas.before:
            Color(*BORDER)
            self._border = Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._sync, size=self._sync)
        Clock.schedule_interval(self._tick, 1 / 60)

    def _sync(self, *_):
        self._border.pos = self.pos
        self._border.size = self.size
        self._fg.pos = self.pos
        self._fg.size = (self.display * self.width, self.height)

    def _tick(self, dt):
        self.display += (self.value - self.display) * min(1, self.speed * dt)
        self._fg.size = (self.display * self.width, self.height)


class _Toast(Label):
    pass


class ToastOverlay(FloatLayout):
    pass


class ToastManager:
    _overlay = None

    @classmethod
    def ensure_overlay(cls):
        if cls._overlay is None:
            app = App.get_running_app()
            if not app or not app.root:
                return
            cls._overlay = ToastOverlay()
            app.root.add_widget(cls._overlay)

    @classmethod
    def show(cls, text: str):
        cls.ensure_overlay()
        app = App.get_running_app()
        if not app or not app.root or not cls._overlay:
            return  # app not ready yet; fail gracefully

        lab = _Toast(text=text)
        lab.size_hint = (None, None)
        lab.opacity = 0
        lab.padding = ("14dp", "10dp")
        lab.base_size = BODY
        lab.texture_update()
        lab.size = (lab.texture_size[0] + 28, lab.texture_size[1] + 20)
        lab.pos_hint = {"center_x": 0.5}
        lab.y = 24
        with lab.canvas.before:
            Color(0, 0, 0, 0.8)
            lab._bg = RoundedRectangle(
                pos=lab.pos, size=lab.size, radius=[12, 12, 12, 12]
            )
        lab.bind(
            pos=lambda *_: setattr(lab._bg, "pos", lab.pos),
            size=lambda *_: setattr(lab._bg, "size", lab.size),
        )
        cls._overlay.add_widget(lab)
        Animation(opacity=1, d=0.15).start(lab)
        Clock.schedule_once(lambda *_: cls._dismiss(lab), TOAST_SECS)

    @classmethod
    def _dismiss(cls, lab):
        """Fade out and remove the toast; safe if overlay went away."""
        try:
            anim = Animation(opacity=0, d=0.2)
            def _remove(*_):
                if cls._overlay and lab.parent is cls._overlay:
                    cls._overlay.remove_widget(lab)
            anim.bind(on_complete=_remove)
            anim.start(lab)
        except Exception:
            # Hard fallback remove
            if cls._overlay and lab.parent is cls._overlay:
                cls._overlay.remove_widget(lab)


class Dialog(ModalView):
    title = StringProperty("")
    message = StringProperty("")
    confirm_text = StringProperty(tr("Confirm"))
    cancel_text = StringProperty(tr("Cancel"))
    on_confirm = ObjectProperty(lambda *_: None)

    def __init__(self, **kw):
        super().__init__(**kw)
        self.background_color = (0, 0, 0, 0.4)
        self.auto_dismiss = False

    def confirm(self):
        try:
            self.on_confirm()
        finally:
            self.dismiss()

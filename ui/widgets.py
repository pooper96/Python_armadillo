from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.button import Button
from kivy.uix.label import Label

ACTIVE_BG = (0.22, 0.65, 0.38, 1)
INACTIVE_BG = (0.3, 0.3, 0.3, 1)
TEXT_COLOR = (1, 1, 1, 1)


class NavButton(Button):
    def __init__(self, **kw):
        kw.setdefault("background_normal", "")
        kw.setdefault("background_down", "")
        kw.setdefault("color", TEXT_COLOR)
        super().__init__(**kw)


class TopBar(BoxLayout):
    services = ObjectProperty(None)
    coins_text = StringProperty("0")

    def __init__(self, services, **kwargs):
        super().__init__(orientation="horizontal", size_hint_y=None, height=48, spacing=6, padding=(8, 6), **kwargs)
        self.services = services

        self.lbl = Label(text="Coins: 0.0", size_hint_x=None, width=150,
                         halign="left", valign="middle", color=TEXT_COLOR)
        self.lbl.bind(size=lambda *_: setattr(self.lbl, "text_size", self.lbl.size))
        self.add_widget(self.lbl)

        self.home_btn = NavButton(text="Home", background_color=INACTIVE_BG)
        self.hab_btn = NavButton(text="Habitats", background_color=INACTIVE_BG)
        self.breed_btn = NavButton(text="Breeding", background_color=INACTIVE_BG)
        self.dex_btn = NavButton(text="Dex", background_color=INACTIVE_BG)
        self.shop_btn = NavButton(text="Shop", background_color=INACTIVE_BG)
        self.settings_btn = NavButton(text="Settings", background_color=INACTIVE_BG)

        self._btn_map = {
            "home": self.home_btn,
            "habitat": self.hab_btn,
            "breeding": self.breed_btn,
            "dex": self.dex_btn,
            "shop": self.shop_btn,
            "settings": self.settings_btn,
        }
        for b in self._btn_map.values():
            self.add_widget(b)

        from kivy.clock import Clock
        Clock.schedule_interval(lambda dt: self._tick_coins(), 0.25)

    def _tick_coins(self):
        if self.services and self.services.sim:
            coins = float(self.services.sim.state.get('coins', 0.0))
            self.lbl.text = f"Coins: {coins:.1f}"

    def set_active(self, screen_name: str):
        for name, btn in self._btn_map.items():
            btn.background_color = ACTIVE_BG if name == screen_name else INACTIVE_BG

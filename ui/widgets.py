from kivy.uix.boxlayout import BoxLayout
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.button import Button
from kivy.uix.label import Label


class TopBar(BoxLayout):
    services = ObjectProperty(None)
    coins_text = StringProperty("0")

    def __init__(self, services, **kwargs):
        super().__init__(orientation="horizontal", size_hint_y=None, height=48, spacing=6, padding=(8, 6), **kwargs)
        self.services = services

        self.lbl = Label(text="Coins: 0", size_hint_x=None, width=150, halign="left", valign="middle")
        self.lbl.bind(size=lambda *_: setattr(self.lbl, "text_size", self.lbl.size))
        self.add_widget(self.lbl)

        self.home_btn = Button(text="Home")
        self.hab_btn = Button(text="Habitats")
        self.breed_btn = Button(text="Breeding")
        self.dex_btn = Button(text="Dex")
        self.shop_btn = Button(text="Shop")
        self.settings_btn = Button(text="Settings")
        for b in (self.home_btn, self.hab_btn, self.breed_btn, self.dex_btn, self.shop_btn, self.settings_btn):
            self.add_widget(b)

        self.bind(coins_text=self._on_coins_text)

    def _on_coins_text(self, *_):
        self.lbl.text = f"Coins: {self.coins_text}"

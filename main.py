# main.py
from __future__ import annotations

import base64
import json
import logging
import os
import time
from typing import Optional

from kivy import __version__ as kivy_version
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.utils import platform

# Prefer KivyMD, but support a Kivy-only fallback.
HAS_MD = True
try:
    from kivymd.app import MDApp
    from kivymd.uix.dialog import MDDialog
    from kivymd.uix.button import MDFlatButton
except Exception:  # KivyMD might be missing on desktop; still run.
    HAS_MD = False
    from kivy.app import App as MDApp  # type: ignore
    MDDialog = None  # type: ignore
    MDFlatButton = None  # type: ignore

from services.state import GameState
from services.persistence import Persistence
from services.economy import Economy
from ui.components import (
    show_toast,
    MDCompatibleScreenManager,
    HomeScreen,
    HabitatsScreen,
    BreedingScreen,
    DexScreen,
    ShopScreen,
    TopBar,
)


APP_TITLE = "Armadillo Farmer"
ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")
ICON_PATH = os.path.join(ASSETS_DIR, "icon.png")
KV_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "kv", "main.kv")


def _ensure_assets() -> None:
    """Write the bundled base64 icon to assets/icon.png if missing."""
    if not os.path.isdir(ASSETS_DIR):
        os.makedirs(ASSETS_DIR, exist_ok=True)
    if not os.path.exists(ICON_PATH):
        # 128x128 simple armadillo icon (flat, dark circle + "A")
        ICON_B64 = (
            "iVBORw0KGgoAAAANSUhEUgAAAIAAAACACAIAAAD8GO2jAAAACXBIWXMAAAsSAAALEgHS3X78AAABl0lEQVR4nO3a"
            "wU3DQBQF0Zc0J2QZ0tY0mCbJ1lOy3gC2l0Yd3GQ9b9Kz4b4g4D5O4KQkR2f8b7x2r+0wq2o1j8i0pBIJgSCTwI6b"
            "V8bNwQGd5Q7r7n4c2y9C0o6i4J3q1f6Dk4nqvQ0E1E4q1m3d2g3kq3wR0B4o2y1f7oG6Czq3j8I0E4o2y1f7oG6Cz"
            "q3j8I0E4o2y1f7oG6Czq3j8Jm6cW7VnCk8cEw8b5jv0P6Q4cEw8b5jv0P6Q4cEw8b5jv0P6S+u7E1c7qQ0d3H2Q5"
            "cGm0o7r5G0cHk0o6r5E0cHk0o6r5E0cHk0qZ7XnV7Wv3gKqY6y4b3+QmA0v9gJb8b2m+g1zU4Qn3o7JwB3iQkZpQ"
            "AAcQmA1gQmA1gQmA1gQmA1gQmA1gQmA1gQmA1gQmA1gQmA1gQmA1gQmA1gQmA1gQmA1gQmA1gQmA1gQmA1gQmA1g"
            "Qq2j9v0UQ5eH3b7o1mG3Y8jQ5gQyV7rj3Y8jQ5gQyV7rj3Y8jQ5gQyV7rj3Y8nWw9F5k8u8TqS1H9NwAAAAASUVO"
            "RK5CYII="
        )
        with open(ICON_PATH, "wb") as f:
            f.write(base64.b64decode(ICON_B64))


class ArmadilloApp(MDApp):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.state = GameState.instance()
        self.persistence = Persistence()
        self.sm: Optional[MDCompatibleScreenManager] = None
        self.topbar: Optional[TopBar] = None
        self._autosave_ev = None

    def build(self):
        logging.basicConfig(level=logging.INFO)
        _ensure_assets()
        self.title = APP_TITLE
        self.icon = ICON_PATH
        if HAS_MD:
            self.theme_cls.theme_style = "Dark"
            self.theme_cls.primary_palette = "Teal"

        # Load KV layout (KivyMD variant). Fallback UI is built in Python when KivyMD missing.
        if HAS_MD:
            Builder.load_file(KV_PATH)

        # Screen manager + screens
        self.sm = MDCompatibleScreenManager()
        self.topbar = TopBar(app=self)
        self.sm.add_widget(HomeScreen(name="home", app=self))
        self.sm.add_widget(HabitatsScreen(name="habitats", app=self))
        self.sm.add_widget(BreedingScreen(name="breeding", app=self))
        self.sm.add_widget(DexScreen(name="dex", app=self))
        self.sm.add_widget(ShopScreen(name="shop", app=self))

        # Prepare root
        root = self.sm.build_root_with_nav(self.topbar)

        # Load / seed state
        self._load_or_seed()

        # Bind state observers
        self.state.add_observer(self._on_state_change)

        # UI refresh tick
        Clock.schedule_interval(lambda dt: self._tick(dt), 0.25)

        # Auto-save throttle
        self._autosave_ev = Clock.create_trigger(lambda *_: self._save(), 0.6)

        # Desktop: make reasonable portrait window
        if platform not in ("android", "ios"):
            Window.size = (420, 780)

        return root

    # ---- Lifecycle ---------------------------------------------------------

    def on_start(self):
        # Show starter tip
        if self.state.meta.get("first_run", False):
            show_toast("Welcome! Tap a card to select, then Feed/Pet. Long-press to drag to a habitat.")

    def on_pause(self):
        self._save()
        return True

    def on_stop(self):
        self._save()

    # ---- Persistence / State ----------------------------------------------

    def _load_or_seed(self):
        ok = self.persistence.load(self.state)
        if not ok or not self.state.armadillos:
            logging.info("Seeding starters...")
            self.state.seed_starters()
            self.state.meta["first_run"] = True
            self._save()
        else:
            self.state.meta["first_run"] = False

    def _save(self):
        self.persistence.save(self.state)

    def _on_state_change(self, *_):
        # Update topbar coins
        if self.topbar:
            self.topbar.update_coin_label(self.state.coins)
        # Queue autosave
        if self._autosave_ev:
            self._autosave_ev()

    # ---- Ticking -----------------------------------------------------------

    def _tick(self, _dt: float):
        # Drive countdowns and UI refresh
        now = time.time()
        hatched = self.state.breeding_tick(now)
        if hatched:
            self._handle_hatch_results(hatched)

        # Refresh screens (lightweight)
        for name in ("home", "habitats", "breeding", "dex", "shop"):
            scr = self.sm.get_screen(name) if self.sm else None
            if scr and hasattr(scr, "refresh"):
                scr.refresh()

    # ---- Game events -------------------------------------------------------

    def _handle_hatch_results(self, results):
        # Award coins + show dialog for every hatched egg
        earned = 0
        for res in results:
            earned += Economy.REWARD_HATCH
        if earned:
            self.state.add_coins(earned)
            show_toast(f"+{earned} coins • Hatched!")
        # Show details
        if HAS_MD and MDDialog:
            lines = "\n".join([f"New {r.color} baby named {r.name}!" for r in results])
            dialog = MDDialog(
                title="Hatch Success",
                text=lines,
                buttons=[MDFlatButton(text="OK", on_release=lambda *a: dialog.dismiss())],
            )
            dialog.open()


if __name__ == "__main__":
    ArmadilloApp().run()

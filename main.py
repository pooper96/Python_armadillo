# main.py
# App bootstrap, GameState model, autosave, ScreenManager, safe areas.
import json, os, random, time
from dataclasses import dataclass, asdict
from typing import List, Dict

from kivy.app import App
from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.properties import (NumericProperty, ListProperty, BooleanProperty, StringProperty)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager, NoTransition

from ui.constants import BG, SAFE_TOP, SAFE_BOT, tr
from ui.drag import DragManager
from ui.widgets import TopBar, BottomNav, ToastManager, log_event

# -------- Minimal GameState --------
class GameState(BoxLayout):
    # Using Properties so kv can bind
    coins = NumericProperty(100)
    # Armadillos: list of dicts {id, name, hunger(0..1), happiness(0..1), pen}
    armadillos = ListProperty([])
    # Pens/Habitats: list of dicts {name, cap, yield, biome}
    pens = ListProperty([])
    # Breeding/incubator queue: list of dicts {egg_id, remain}
    incubator = ListProperty([])
    inc_slots = NumericProperty(1)
    version = StringProperty("1")

    def __init__(self, **kw):
        super().__init__(**kw)
        if not self.pens:
            self.pens = [
                {"name": "Meadow", "cap": 6, "yield": 1.0, "biome":"grass"},
                {"name": "Dunes",  "cap": 6, "yield": 1.1, "biome":"sand"},
                {"name": "Marsh",  "cap": 6, "yield": 1.2, "biome":"wet"},
            ]
        if not self.armadillos:
            self.armadillos = [
                {"id": "A1", "name": "Rollo", "hunger": .2, "happiness": .8, "pen": 0},
                {"id": "A2", "name": "Pip",   "hunger": .5, "happiness": .5, "pen": 0},
                {"id": "A3", "name": "Mara",  "hunger": .7, "happiness": .3, "pen": 1},
            ]
        self.dex_items = [
            {"id":"D1","name":"Common Armadillo","rarity":"Common","biome":"grass","found":True},
            {"id":"D2","name":"Golden Dillo","rarity":"Rare","biome":"sand","found":False},
        ]

    # ---- Persistence ----
    def to_dict(self):
        return {
            "version": self.version,
            "coins": int(self.coins),
            "armadillos": list(self.armadillos),
            "pens": list(self.pens),
            "incubator": list(self.incubator),
            "inc_slots": int(self.inc_slots),
        }

    def from_dict(self, data: Dict):
        self.version = str(data.get("version", "1"))
        self.coins = data.get("coins", 0)
        self.armadillos = data.get("armadillos", [])
        self.pens = data.get("pens", [])
        self.incubator = data.get("incubator", [])
        self.inc_slots = data.get("inc_slots", 1)

    def reset(self):
        self.__init__()

    # ---- Coins ----
    def add_coins(self, n: int):
        self.coins += int(n)

    def spend_coins(self, n: int) -> bool:
        if self.coins >= n:
            self.coins -= n
            return True
        return False

    # ---- Armadillo actions ----
    def _find(self, a_id: str):
        for a in self.armadillos:
            if a["id"] == a_id:
                return a
        return None

    def can_place(self, a_id: str, pen_index: int) -> bool:
        cap = self.pens[pen_index]["cap"]
        used = sum(1 for a in self.armadillos if a["pen"] == pen_index)
        return used < cap

    def move_armadillo(self, a_id: str, pen_index: int) -> bool:
        a = self._find(a_id)
        if not a or not self.can_place(a_id, pen_index):
            return False
        a["pen"] = int(pen_index)
        return True

    def feed(self, a_id: str) -> bool:
        a = self._find(a_id)
        if not a: return False
        if a["hunger"] <= 0.01: return False
        a["hunger"] = max(0.0, a["hunger"] - 0.25)
        self.add_coins(1)
        return True

    def pet(self, a_id: str) -> bool:
        a = self._find(a_id)
        if not a: return False
        if a["happiness"] >= 0.99: return False
        a["happiness"] = min(1.0, a["happiness"] + 0.2)
        return True

    def upgrade_habitat(self, idx: int) -> bool:
        if not self.spend_coins(20):
            return False
        self.pens[idx]["cap"] += 1
        return True

    # ---- Breeding/incubation ----
    def start_breed(self, a_id: str, b_id: str) -> bool:
        if len(self.incubator) >= self.inc_slots:
            return False
        self.incubator.append({"egg_id": f"egg_{int(time.time())}", "remain": 20.0})
        return True

    def advance_incubators(self, seconds: float) -> bool:
        changed = False
        for q in self.incubator:
            if q["remain"] > 0:
                q["remain"] = max(0.0, q["remain"] - seconds)
                changed = True
        # hatch any done
        done = [q for q in self.incubator if q["remain"] <= 0]
        if done:
            for _ in done:
                # create a baby
                new_id = f"A{len(self.armadillos)+1}"
                self.armadillos.append({"id": new_id, "name": "Baby", "hunger": .6, "happiness": .6, "pen": 0})
                self.add_coins(5)
            self.incubator = [q for q in self.incubator if q["remain"] > 0]
            ToastManager.show(tr("Hatched!"))
        return changed

    def speed_up_incubator(self, idx: int, seconds: float = 10.0):
        if 0 <= idx < len(self.incubator):
            self.incubator[idx]["remain"] = max(0.0, self.incubator[idx]["remain"] - seconds)

# -------- Root (chrome + navigation) --------
class Root(BoxLayout):
    def __init__(self, **kw):
        super().__init__(**kw)
        self.orientation = "vertical"
        # Safe area padding (top/bottom)
        self.padding = (0, SAFE_BOT, 0, SAFE_TOP)
        # top bar
        self.topbar = TopBar(title="Armadillo", on_settings=self.open_settings)
        self.add_widget(self.topbar)
        # screens
        self.sm = ScreenManager(transition=NoTransition())
        # Import screen classes so kv can use them
        from ui.screens.home import HomeScreen  # noqa
        from ui.screens.habitats import HabitatsScreen  # noqa
        from ui.screens.breeding import BreedingScreen  # noqa
        from ui.screens.dex import DexScreen  # noqa
        from ui.screens.shop import ShopScreen  # noqa

        # Load kv layout
        from kivy.factory import Factory

        Builder.load_file("ui/layout.kv")

        # Try template first, fall back to Factory instantiation
        def add(name):
            try:
                self.sm.add_widget(Builder.template(name))
            except Exception:
                self.sm.add_widget(getattr(Factory, name)())

        for name in ["HomeScreen", "HabitatsScreen", "BreedingScreen", "DexScreen", "ShopScreen"]:
            add(name)

        self.add_widget(self.sm)
        # bottom nav
        self.nav = BottomNav(on_tab=self.switch_to)
        self.add_widget(self.nav)
        # drag overlay + toast overlay
        DragManager.attach(self)

    def switch_to(self, tab: str):
        self.nav.current = tab
        self.sm.current = tab

    def open_settings(self):
        self.sm.current = "shop"  # lightweight: settings icon could route to settings screen if present
        App.get_running_app().open_settings_screen()

# -------- App --------
class ArmadilloApp(App):
    music = BooleanProperty(True)
    sfx = BooleanProperty(True)
    haptics = BooleanProperty(True)
    reduce_motion = BooleanProperty(False)
    large_text = BooleanProperty(False)

    def __init__(self, **kw):
        super().__init__(**kw)
        self.state = GameState()
        self._save_ev = None

    def build(self):
        self.title = "Armadillo"
        Window.clearcolor = BG
        self._load_if_exists()
        root = Root()
        self.root = root
        ToastManager.ensure_overlay()
        return root

    # -------- Navigation helpers --------
    def open_settings_screen(self):
        # If you add a dedicated settings screen, switch here.
        pass

    # -------- Autosave --------
    @property
    def save_path(self):
        return os.path.join(self.user_data_dir, "save.json")

    def autosave_later(self, delay=0.2):
        if self._save_ev:
            self._save_ev.cancel()
        self._save_ev = Clock.schedule_once(lambda dt: self._save_now(), delay)

    def _save_now(self):
        os.makedirs(self.user_data_dir, exist_ok=True)
        with open(self.save_path, "w", encoding="utf-8") as f:
            json.dump(self.state.to_dict(), f, ensure_ascii=False)
        log_event("autosave")

    def _load_if_exists(self):
        try:
            with open(self.save_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.state.from_dict(data)
        except Exception:
            pass

    # Android lifecycle
    def on_pause(self):
        self._save_now()
        return True

    def on_resume(self):
        # no-op; state already in memory
        pass

if __name__ == "__main__":
    ArmadilloApp().run()

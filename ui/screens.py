from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle, Ellipse
from kivy.clock import Clock

from ui.widgets import TopBar
from models.armadillo import Armadillo
from models.genetics import RNG


class BaseScreen(Screen):
    def __init__(self, services, **kwargs):
        super().__init__(**kwargs)
        self.services = services

    def on_pre_enter(self, *args):
        self.refresh()

    def refresh(self):
        pass


class HomeScreen(BaseScreen):
    def __init__(self, services, **kwargs):
        super().__init__(services, **kwargs)
        self.root_box = BoxLayout(orientation="vertical")
        self.topbar = TopBar(services)
        self.root_box.add_widget(self.topbar)
        self.canvas_box = BoxLayout()
        self.root_box.add_widget(self.canvas_box)
        self.add_widget(self.root_box)

        # Navigation bindings
        self.topbar.home_btn.bind(on_release=lambda *_: setattr(self.manager, "current", "home"))
        self.topbar.hab_btn.bind(on_release=lambda *_: setattr(self.manager, "current", "habitat"))
        self.topbar.breed_btn.bind(on_release=lambda *_: setattr(self.manager, "current", "breeding"))
        self.topbar.dex_btn.bind(on_release=lambda *_: setattr(self.manager, "current", "dex"))
        self.topbar.shop_btn.bind(on_release=lambda *_: setattr(self.manager, "current", "shop"))
        self.topbar.settings_btn.bind(on_release=lambda *_: setattr(self.manager, "current", "settings"))

        Clock.schedule_interval(lambda dt: self._update_topbar(), 0.25)

    def _update_topbar(self):
        self.topbar.coins_text = str(int(self.services.sim.state["coins"]))

    def refresh(self):
        self.canvas_box.canvas.clear()
        with self.canvas_box.canvas:
            # simple parallax-ish background layers
            w = self.services.settings.SCREEN_W
            h = self.services.settings.SCREEN_H - 40
            Color(0.65, 0.85, 1.0, 1.0); Rectangle(pos=self.pos, size=(w, h))           # sky
            Color(0.85, 0.8, 0.6, 1.0); Rectangle(pos=(0, 0), size=(w, h * 0.35))       # far sand
            Color(0.9, 0.8, 0.55, 1.0); Rectangle(pos=(0, 0), size=(w, h * 0.25))       # near sand

            # draw some armadillos in a row
            x = 40
            for a in self.services.sim.get_armadillos()[:6]:
                r, g, b = a.rgb
                # shadow
                Color(0, 0, 0, self.services.settings.SHADOW_ALPHA)
                Ellipse(pos=(x, 70), size=(70, 20))
                # body
                Color(r, g, b, 1.0)
                Ellipse(pos=(x, 90), size=(70, 45))
                # head
                Ellipse(pos=(x + 50, 110), size=(25, 20))
                x += 110


class HabitatScreen(BaseScreen):
    def __init__(self, services, **kwargs):
        super().__init__(services, **kwargs)
        layout = BoxLayout(orientation="vertical", spacing=6, padding=6)
        self.topbar = TopBar(services)
        layout.add_widget(self.topbar)
        self.lbl = Label(text="Habitats and residents")
        layout.add_widget(self.lbl)
        self.add_widget(layout)

        Clock.schedule_interval(lambda dt: self._update_topbar(), 0.25)

    def _update_topbar(self):
        self.topbar.coins_text = str(int(self.services.sim.state["coins"]))

    def refresh(self):
        arms = self.services.sim.get_armadillos()
        habs = self.services.sim.get_habitats()
        summary = []
        for h in habs:
            occupants = [a for a in arms if a.habitat_id == h.id]
            summary.append(f"{h.name} ({h.biome}) {len(occupants)}/{h.capacity}")
        self.lbl.text = "\n".join(summary) if summary else "No habitats yet."


class BreedingScreen(BaseScreen):
    def __init__(self, services, **kwargs):
        super().__init__(services, **kwargs)
        self.box = BoxLayout(orientation="vertical", spacing=6, padding=6)
        self.topbar = TopBar(services)
        self.box.add_widget(self.topbar)
        self.lbl = Label(text="Select first two adults to breed.")
        self.box.add_widget(self.lbl)
        self.action_btn = Button(text="Breed first M+F adults (demo)")
        self.box.add_widget(self.action_btn)
        self.add_widget(self.box)

        self.action_btn.bind(on_release=lambda *_: self._breed_demo())
        Clock.schedule_interval(lambda dt: self._update_topbar(), 0.25)

    def _update_topbar(self):
        self.topbar.coins_text = str(int(self.services.sim.state["coins"]))

    def _breed_demo(self):
        arms = [a for a in self.services.sim.get_armadillos() if a.stage == "adult"]
        mom = next((x for x in arms if x.sex == "F"), None)
        dad = next((x for x in arms if x.sex == "M"), None)
        if not (mom and dad):
            self.lbl.text = "Need an adult M and F."
            return
        child = Armadillo.breed(self.services.settings, mom, dad)
        st = self.services.sim.state
        st["armadillos"].append(child.to_dict())
        # No immediate disk write; autosave will catch it
        self.lbl.text = f"New egg! Color {child.hex_color}"

    def refresh(self):
        arms = self.services.sim.get_armadillos()
        adults = [a for a in arms if a.stage == "adult"]
        self.lbl.text = f"Adults ready: {len(adults)}"


class DexScreen(BaseScreen):
    def __init__(self, services, **kwargs):
        super().__init__(services, **kwargs)
        self.box = BoxLayout(orientation="vertical", spacing=6, padding=6)
        self.topbar = TopBar(services)
        self.box.add_widget(self.topbar)
        self.lbl = Label(text="Dex/Collection")
        self.box.add_widget(self.lbl)
        self.add_widget(self.box)
        Clock.schedule_interval(lambda dt: self._update_topbar(), 0.25)

    def _update_topbar(self):
        self.topbar.coins_text = str(int(self.services.sim.state["coins"]))

    def refresh(self):
        arms = self.services.sim.get_armadillos()
        lines = []
        for a in arms[:12]:
            tag = ""
            if self.services.settings.ENABLE_COLORBLIND_NUMERIC_TAGS:
                r, g, b = a.rgb
                tag = f" [{int(r*255)}/{int(g*255)}/{int(b*255)}]"
            lines.append(f"{a.nickname} {a.stage} {a.sex} {a.hex_color}{tag}")
        self.lbl.text = "\n".join(lines) if lines else "No armadillos yet."


class ShopScreen(BaseScreen):
    def __init__(self, services, **kwargs):
        super().__init__(services, **kwargs)
        self.box = BoxLayout(orientation="vertical", spacing=6, padding=6)
        self.topbar = TopBar(services)
        self.box.add_widget(self.topbar)
        self.info = Label(text="Shop: Feed (2 coins). Feeding slightly adjusts weight.\nTap to feed the first non-egg.")
        self.box.add_widget(self.info)
        self.feed_btn = Button(text="Feed first non-egg (demo)")
        self.box.add_widget(self.feed_btn)
        self.add_widget(self.box)
        self.feed_btn.bind(on_release=lambda *_: self._feed_demo())
        Clock.schedule_interval(lambda dt: self._update_topbar(), 0.25)

    def _update_topbar(self):
        self.topbar.coins_text = str(int(self.services.sim.state["coins"]))

    def _feed_demo(self):
        st = self.services.sim.state
        if not self.services.econ.spend(self.services.econ.feed_cost()):
            self.info.text = "Not enough coins."
            return
        arms = self.services.sim.get_armadillos()
        target = next((a for a in arms if a.stage != "egg"), None)
        if not target:
            self.info.text = "No valid target."
            return
        target.weight = max(0.5, min(1.5, target.weight + (RNG.random() - 0.5) * 0.1))
        self.services.sim.set_armadillos(arms)
        # No immediate disk write; autosave will catch it
        self.info.text = f"Fed {target.nickname}. New weight: {target.weight:.2f}"

    def refresh(self):
        pass


class SettingsScreen(BaseScreen):
    def __init__(self, services, **kwargs):
        super().__init__(services, **kwargs)
        self.box = BoxLayout(orientation="vertical", spacing=6, padding=6)
        self.topbar = TopBar(services)
        self.box.add_widget(self.topbar)
        self.lbl = Label(text="Settings (demo)")
        self.box.add_widget(self.lbl)
        self.add_widget(self.box)

    def refresh(self):
        pass

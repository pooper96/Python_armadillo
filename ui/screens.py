from __future__ import annotations
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle, Line
from kivy.clock import Clock

from models.armadillo import Armadillo
from models.genetics import RNG


class BaseScreen(Screen):
    def __init__(self, services, **kwargs):
        super().__init__(**kwargs)
        self.services = services

    def refresh(self):
        pass


class HomeScreen(BaseScreen):
    """Farm view with crisp pixel-armadillo sprites (nearest-neighbor scale)."""
    def __init__(self, services, **kwargs):
        super().__init__(services, **kwargs)
        self.root_box = BoxLayout(orientation="vertical")
        self.canvas_box = BoxLayout()
        self.root_box.add_widget(self.canvas_box)
        self.add_widget(self.root_box)

        # redraw on resize
        self.canvas_box.bind(size=lambda *_: self.refresh(), pos=lambda *_: self.refresh())

        # runtime anim state (id -> dict)
        self._sprites = {}
        Clock.schedule_interval(self._animate, 1 / 60.0)

    # -------- animation state ------
    def _ensure_sprites(self):
        cb = self.canvas_box
        w, h = cb.size
        if w < 10 or h < 10:
            return
        base_y = cb.y + h * 0.16  # near ground band
        for a in self.services.sim.get_armadillos():
            if a.id not in self._sprites:
                frames = self.services.assets.armadillo_frames(a.rgb)
                # spawn roughly across the ground
                x = RNG.uniform(cb.x + 40, cb.x + w - 40)
                vx = RNG.uniform(self.services.settings.ARM_SPEED_MIN, self.services.settings.ARM_SPEED_MAX)
                if RNG.randint(0, 1) == 0:
                    vx = -vx
                self._sprites[a.id] = {
                    "x": x,
                    "y": base_y,
                    "vx": vx,
                    "t": 0.0,
                    "frames": frames,
                    "frame_i": 0,
                }

    def _animate(self, dt):
        self._ensure_sprites()
        cb = self.canvas_box
        w, h = cb.size
        if w < 10 or h < 10:
            return

        left = cb.x + self.services.settings.ARM_MARGIN_X
        right = cb.x + w - self.services.settings.ARM_MARGIN_X
        for a in self.services.sim.get_armadillos()[:12]:
            s = self._sprites[a.id]
            s["t"] += dt
            # movement + bounce
            s["x"] += s["vx"] * dt
            if s["x"] < left:
                s["x"] = left
                s["vx"] = abs(s["vx"])
            elif s["x"] > right:
                s["x"] = right
                s["vx"] = -abs(s["vx"])
            # 2-frame walk every ~0.25s
            if s["t"] >= 0.25:
                s["frame_i"] = 1 - s["frame_i"]
                s["t"] = 0.0

        self._draw()

    # -------- drawing -----------
    def refresh(self):
        self._ensure_sprites()
        self._draw()

    def _draw(self):
        cb = self.canvas_box
        w, h = cb.size
        x0, y0 = cb.pos
        if w < 10 or h < 10:
            return

        sky_h = h * 0.65
        mid_h = h * 0.19
        near_h = h * 0.16

        cb.canvas.clear()
        with cb.canvas:
            # sky stripes
            Color(0.60, 0.84, 1.0, 1.0); Rectangle(pos=(x0, y0 + h - sky_h), size=(w, sky_h))
            Color(0.55, 0.80, 0.98, 1.0); Rectangle(pos=(x0, y0 + h - sky_h * 0.55), size=(w, sky_h * 0.2))
            Color(0.53, 0.78, 0.96, 1.0); Rectangle(pos=(x0, y0 + h - sky_h * 0.80), size=(w, sky_h * 0.15))

            # dunes
            Color(0.86, 0.80, 0.58, 1.0); Rectangle(pos=(x0, y0 + near_h), size=(w, mid_h))
            Color(0.92, 0.84, 0.60, 1.0); Rectangle(pos=(x0, y0), size=(w, near_h))

            # fence line
            Color(0.35, 0.28, 0.18, 1.0)
            Line(points=[x0, y0 + near_h + 6, x0 + w, y0 + near_h + 6], width=1.3)

            # sprites
            scale = max(3.0, min(8.0, w / 180.0))  # pixel size
            spw, sph = 16 * scale, 12 * scale
            ground_y = y0 + near_h - 2  # sit slightly into the sand
            for a in self.services.sim.get_armadillos()[:12]:
                s = self._sprites[a.id]
                tex = s["frames"][s["frame_i"]]
                # When going left, flip by using negative width
                width = spw if s["vx"] >= 0 else -spw
                px = s["x"] - (spw / 2 if s["vx"] >= 0 else -spw / 2)
                Rectangle(texture=tex, pos=(px, ground_y), size=(width, sph))


class HabitatScreen(BaseScreen):
    def __init__(self, services, **kwargs):
        super().__init__(services, **kwargs)
        layout = BoxLayout(orientation="vertical", spacing=6, padding=12)
        self.lbl = Label(text="Habitats and residents")
        layout.add_widget(self.lbl)
        self.add_widget(layout)

    def on_pre_enter(self, *args):
        self.refresh()

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
        self.box = BoxLayout(orientation="vertical", spacing=12, padding=12)
        self.lbl = Label(text="Select first two adults to breed.")
        self.box.add_widget(self.lbl)
        self.action_btn = Button(text="Breed first M+F adults (demo)")
        self.box.add_widget(self.action_btn)
        self.add_widget(self.box)

        self.action_btn.bind(on_release=lambda *_: self._breed_demo())

    def on_pre_enter(self, *args):
        self.refresh()

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
        self.lbl.text = f"New egg! Color {child.hex_color}"

    def refresh(self):
        arms = self.services.sim.get_armadillos()
        adults = [a for a in arms if a.stage == "adult"]
        self.lbl.text = f"Adults ready: {len(adults)}"


class DexScreen(BaseScreen):
    def __init__(self, services, **kwargs):
        super().__init__(services, **kwargs)
        self.box = BoxLayout(orientation="vertical", spacing=6, padding=12)
        self.lbl = Label(text="Dex/Collection")
        self.box.add_widget(self.lbl)
        self.add_widget(self.box)

    def on_pre_enter(self, *args):
        self.refresh()

    def refresh(self):
        arms = self.services.sim.get_armadillos()
        lines = []
        for a in arms[:12]:
            r, g, b = a.rgb
            tag = f" [{int(r*255)}/{int(g*255)}/{int(b*255)}]"
            lines.append(f"{a.nickname} {a.stage} {a.sex} {a.hex_color}{tag}")
        self.lbl.text = "\n".join(lines) if lines else "No armadillos yet."


class ShopScreen(BaseScreen):
    def __init__(self, services, **kwargs):
        super().__init__(services, **kwargs)
        self.box = BoxLayout(orientation="vertical", spacing=12, padding=12)
        self.info = Label(text="Shop: Feed (2 coins). Feeding slightly adjusts weight.\nTap to feed the first non-egg.")
        self.box.add_widget(self.info)
        self.feed_btn = Button(text="Feed first non-egg (demo)")
        self.box.add_widget(self.feed_btn)
        self.add_widget(self.box)
        self.feed_btn.bind(on_release=lambda *_: self._feed_demo())

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
        self.info.text = f"Fed {target.nickname}. New weight: {target.weight:.2f}"


class SettingsScreen(BaseScreen):
    def __init__(self, services, **kwargs):
        super().__init__(services, **kwargs)
        self.box = BoxLayout(orientation="vertical", spacing=6, padding=12)
        self.lbl = Label(text="Settings (demo)")
        self.box.add_widget(self.lbl)
        self.add_widget(self.box)

    def on_pre_enter(self, *args):
        self.refresh()

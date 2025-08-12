from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.graphics import Color, Rectangle, Ellipse, Line
from kivy.clock import Clock

from ui.widgets import TopBar
from models.armadillo import Armadillo
from models.genetics import RNG


class BaseScreen(Screen):
    def __init__(self, services, **kwargs):
        super().__init__(**kwargs)
        self.services = services

    def on_pre_enter(self, *args):
        # child screens override and call topbar.set_active(...)
        self.refresh()

    def refresh(self):
        pass


class HomeScreen(BaseScreen):
    """Farm view: responsive background + idle armadillos that waddle and bob."""
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

        # redraw when resized or moved
        self.canvas_box.bind(size=lambda *_: self.refresh(), pos=lambda *_: self.refresh())
        Clock.schedule_interval(lambda dt: self._update_topbar(), 0.25)

        # simple runtime animation state (not saved)
        self._sprites = {}  # id -> {"x","y","vx","phase"}
        Clock.schedule_interval(self._animate, 1 / 60.0)

    def on_pre_enter(self, *args):
        super().on_pre_enter(*args)
        self.topbar.set_active("home")

    def _update_topbar(self):
        self.topbar.coins_text = str(int(self.services.sim.state["coins"]))

    # ---------- animation ----------
    def _ensure_sprites(self):
        cb = self.canvas_box
        w, h = cb.size
        near_h = h * 0.22
        base_y = cb.y + near_h

        for a in self.services.sim.get_armadillos():
            if a.id not in self._sprites:
                x = cb.x + RNG.uniform(cb.x + 40, cb.x + max(120, w * 0.8))
                vx = RNG.uniform(self.services.settings.ARM_SPEED_MIN, self.services.settings.ARM_SPEED_MAX)
                if RNG.randint(0, 1) == 0:
                    vx = -vx
                self._sprites[a.id] = {"x": x, "y": base_y, "vx": vx, "phase": RNG.uniform(0, 6.28)}

    def _animate(self, dt):
        # move + bounce, then redraw
        self._ensure_sprites()
        cb = self.canvas_box
        w, h = cb.size
        if w <= 2 or h <= 2:
            return

        left = cb.x + self.services.settings.ARM_MARGIN_X
        right = cb.x + w - self.services.settings.ARM_MARGIN_X
        base_y = cb.y + h * 0.22

        for a in self.services.sim.get_armadillos()[:8]:
            s = self._sprites[a.id]
            s["x"] += s["vx"] * dt
            s["phase"] += 2 * 3.14159 * self.services.settings.ARM_BOB_FREQ * dt
            # bounce
            if s["x"] < left:
                s["x"] = left
                s["vx"] = abs(s["vx"])
            elif s["x"] > right:
                s["x"] = right
                s["vx"] = -abs(s["vx"])
            s["y"] = base_y + self.services.settings.ARM_BOB_AMPLITUDE * (0.5 * (1 + __import__("math").sin(s["phase"])))
        # draw
        self._draw_home()

    # ---------- draw ----------
    def refresh(self):
        # called on enter / resize
        self._ensure_sprites()
        self._draw_home()

    def _draw_home(self):
        cb = self.canvas_box
        w, h = cb.size
        x0, y0 = cb.pos
        if w <= 2 or h <= 2:
            return

        sky_h = h * 0.60
        mid_h = h * 0.18
        near_h = h * 0.22

        cb.canvas.clear()
        with cb.canvas:
            # sky gradient (two rectangles)
            Color(0.60, 0.84, 1.0, 1.0); Rectangle(pos=(x0, y0 + h - sky_h), size=(w, sky_h))
            Color(0.55, 0.80, 0.98, 1.0); Rectangle(pos=(x0, y0 + h - sky_h * 0.55), size=(w, sky_h * 0.25))

            # dunes (middle + near)
            Color(0.86, 0.80, 0.58, 1.0); Rectangle(pos=(x0, y0 + near_h), size=(w, mid_h))
            Color(0.92, 0.84, 0.60, 1.0); Rectangle(pos=(x0, y0), size=(w, near_h))

            # fence line for visual depth
            Color(0.35, 0.28, 0.18, 1.0)
            y_fence = y0 + near_h + 6
            Line(points=[x0, y_fence, x0 + w, y_fence], width=1.4)

            # armadillos (animated positions)
            for a in self.services.sim.get_armadillos()[:8]:
                s = self._sprites[a.id]
                r, g, b = a.rgb

                # shadow (squash based on x-velocity magnitude)
                vel_scale = min(1.0, abs(s["vx"]) / self.services.settings.ARM_SPEED_MAX)
                shadow_w = max(w * 0.06, w * 0.06 + 12 * vel_scale)
                shadow_h = max(h * 0.025, h * 0.025 + 6 * vel_scale)
                Color(0, 0, 0, self.services.settings.SHADOW_ALPHA)
                Ellipse(pos=(s["x"] - shadow_w * 0.5, y0 + near_h * 0.25 - shadow_h * 0.5), size=(shadow_w, shadow_h))

                # body + head (simple “2.5D” ovals)
                Color(r, g, b, 1.0)
                Ellipse(pos=(s["x"] - w * 0.035, s["y"]), size=(w * 0.07, h * 0.06))
                Ellipse(pos=(s["x"] + w * 0.025, s["y"] + h * 0.02), size=(w * 0.03, h * 0.03))

    # end HomeScreen


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

    def on_pre_enter(self, *args):
        super().on_pre_enter(*args)
        self.topbar.set_active("habitat")

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

    def on_pre_enter(self, *args):
        super().on_pre_enter(*args)
        self.topbar.set_active("breeding")

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

    def on_pre_enter(self, *args):
        super().on_pre_enter(*args)
        self.topbar.set_active("dex")

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

    def on_pre_enter(self, *args):
        super().on_pre_enter(*args)
        self.topbar.set_active("shop")

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

    def on_pre_enter(self, *args):
        super().on_pre_enter(*args)
        self.topbar.set_active("settings")

    def refresh(self):
        pass

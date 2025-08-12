from __future__ import annotations
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.progressbar import ProgressBar
from kivy.graphics import Color, Rectangle, Line
from kivy.clock import Clock

from models.armadillo import Armadillo
from models.habitat import Habitat
from models.genetics import RNG


class BaseScreen(Screen):
    def __init__(self, services, **kwargs):
        super().__init__(**kwargs)
        self.services = services

    def refresh(self): ...
# ---------------- Farm ----------------

class HomeScreen(BaseScreen):
    """Farm view: pixel sprites, selection outline, quick actions, drag-to-habitat."""
    def __init__(self, services, **kwargs):
        super().__init__(services, **kwargs)
        self.root_box = BoxLayout(orientation="vertical")
        self.canvas_box = BoxLayout()
        self.root_box.add_widget(self.canvas_box)

        self.action_bar = BoxLayout(orientation="horizontal", size_hint_y=None, height=56, padding=8, spacing=8)
        self.info_lbl = Label(text="Tap to select. Long-press to drag into a habitat slot.", halign="left", valign="middle")
        self.info_lbl.bind(size=lambda *_: setattr(self.info_lbl, "text_size", self.info_lbl.size))
        self.feed_btn = Button(text="Feed (+Hunger)")
        self.pet_btn = Button(text="Pet (+Happiness)")
        self.action_bar.add_widget(self.info_lbl)
        self.action_bar.add_widget(self.feed_btn)
        self.action_bar.add_widget(self.pet_btn)
        self.root_box.add_widget(self.action_bar)
        self.add_widget(self.root_box)

        self.feed_btn.bind(on_release=lambda *_: self._feed_selected())
        self.pet_btn.bind(on_release=lambda *_: self._pet_selected())

        # draw/resize
        self.canvas_box.bind(size=self._on_canvas_change, pos=self._on_canvas_change)

        # runtime state
        self._sprites = {}          # arm_id -> dict(frames, x, vx, frame, rect)
        self._hab_zones = []        # list of dict(id, rect)
        self._long_press_ev = None  # ClockEvent or None

        Clock.schedule_interval(self._animate, 1 / 60.0)

    # ---- helpers ----
    def _on_canvas_change(self, *_):
        # avoid calling refresh before we are fully constructed
        if hasattr(self, "_sprites"):
            self.refresh()

    def _selected_id(self):
        return self.services.ui.selected_armadillo_id

    def _update_action_bar(self):
        sid = self._selected_id()
        if not sid:
            self.info_lbl.text = "Tap to select. Long-press to drag into a habitat slot."
            self.feed_btn.disabled = True
            self.pet_btn.disabled = True
            return
        a = next((x for x in self.services.sim.get_armadillos() if x.id == sid), None)
        if not a:
            self.info_lbl.text = "Tap to select. Long-press to drag into a habitat slot."
            self.feed_btn.disabled = True
            self.pet_btn.disabled = True
            return
        self.feed_btn.disabled = False
        self.pet_btn.disabled = False
        self.info_lbl.text = f"{a.nickname} | Hunger {int(a.hunger)}  | Happiness {int(a.happiness)}"

    # ---------- input / drag ----------
    def _schedule_longpress(self, touch, arm_id):
        def start_drag(_dt):
            ui = self.services.ui
            if ui._drag_touch_uid is not None:
                return
            ui.dragging_id = arm_id
            ui._drag_touch_uid = touch.uid
            ui._drag_started = True
            ui.drag_pos = touch.pos
            # also mark as selected
            ui.selected_armadillo_id = arm_id
            self._update_action_bar()
        self._long_press_ev = Clock.schedule_once(start_drag, 0.25)

    def on_touch_down(self, touch):
        if not self.collide_point(*touch.pos):
            return super().on_touch_down(touch)

        # check armadillo hit
        for a in self.services.sim.get_armadillos()[:16]:
            s = self._sprites.get(a.id)
            if not s:
                continue
            x, y, w, h = s["rect"]
            if x <= touch.x <= x + w and y <= touch.y <= y + h:
                self.services.ui.selected_armadillo_id = a.id
                self._update_action_bar()
                self._schedule_longpress(touch, a.id)
                return True

        # tap empty ground
        self.services.ui.selected_armadillo_id = None
        self._update_action_bar()
        return True

    def on_touch_move(self, touch):
        ui = self.services.ui
        if ui._drag_touch_uid == touch.uid and ui._drag_started:
            ui.drag_pos = touch.pos
            return True
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self._long_press_ev:
            self._long_press_ev.cancel()
            self._long_press_ev = None

        ui = self.services.ui
        if ui._drag_touch_uid == touch.uid and ui._drag_started:
            # drop into habitat zone if any
            for z in self._hab_zones:
                zx, zy, zw, zh = z["rect"]
                if zx <= touch.x <= zx + zw and zy <= touch.y <= zy + zh:
                    self._try_move_to_habitat(ui.dragging_id, z["id"])
                    break
            # reset drag state
            ui._drag_touch_uid = None
            ui._drag_started = False
            ui.dragging_id = None
            return True
        return super().on_touch_up(touch)

    # ---------- quick actions ----------
    def _feed_selected(self):
        sid = self._selected_id()
        if not sid: return
        a = next((x for x in self.services.sim.get_armadillos() if x.id == sid), None)
        if not a: return
        if not self.services.econ.spend(self.services.settings.FEED_COST):
            self.info_lbl.text = "Not enough coins."
            return
        a.hunger = min(self.services.settings.HUNGER_MAX, int(a.hunger + self.services.settings.FEED_HUNGER_GAIN))
        arms = self.services.sim.get_armadillos()
        for i, old in enumerate(arms):
            if old.id == a.id: arms[i] = a
        self.services.sim.set_armadillos(arms)
        self._update_action_bar()

    def _pet_selected(self):
        sid = self._selected_id()
        if not sid: return
        a = next((x for x in self.services.sim.get_armadillos() if x.id == sid), None)
        if not a: return
        a.happiness = min(self.services.settings.HAPPINESS_MAX, int(a.happiness + self.services.settings.PET_HAPPINESS_GAIN))
        arms = self.services.sim.get_armadillos()
        for i, old in enumerate(arms):
            if old.id == a.id: arms[i] = a
        self.services.sim.set_armadillos(arms)
        self._update_action_bar()

    def _try_move_to_habitat(self, arm_id: str | None, hab_id: str):
        if not arm_id:
            self.info_lbl.text = "No armadillo selected."
            return
        arms = self.services.sim.get_armadillos()
        a = next((x for x in arms if x.id == arm_id), None)
        if not a:
            self.info_lbl.text = "Not found."
            return
        habs = self.services.sim.get_habitats()
        h = next((hh for hh in habs if hh.id == hab_id), None)
        if not h:
            self.info_lbl.text = "Habitat missing."
            return
        occupants = [x for x in arms if x.habitat_id == h.id]
        if len(occupants) >= h.capacity:
            self.info_lbl.text = f"{h.name} is full."
            return
        a.habitat_id = h.id
        for i, old in enumerate(arms):
            if old.id == a.id: arms[i] = a
        self.services.sim.set_armadillos(arms)
        self.info_lbl.text = f"Moved {a.nickname} → {h.name}"
        self.refresh()

    # ---------- animation ----------
    def _ensure_sprites(self):
        cb = self.canvas_box
        w, h = cb.size
        if w < 10 or h < 10:
            return
        for a in self.services.sim.get_armadillos():
            if a.id not in self._sprites:
                frames = self.services.assets.armadillo_frames(a.rgb)
                x = RNG.uniform(cb.x + 40, cb.x + w - 40)
                vx = RNG.uniform(self.services.settings.ARM_SPEED_MIN, self.services.settings.ARM_SPEED_MAX)
                if RNG.randint(0, 1) == 0:
                    vx = -vx
                self._sprites[a.id] = {"x": x, "vx": vx, "t": 0.0, "frame": 0, "frames": frames, "rect": (0,0,0,0)}

    def _animate(self, dt):
        self._ensure_sprites()
        cb = self.canvas_box
        w, h = cb.size
        if w < 10 or h < 10:
            return
        left = cb.x + self.services.settings.ARM_MARGIN_X
        right = cb.x + w - self.services.settings.ARM_MARGIN_X

        sset = self.services.settings
        for a in self.services.sim.get_armadillos()[:16]:
            s = self._sprites[a.id]
            # hunger affects base speed strongly; happiness adds bonus
            hunger_mult = sset.SPEED_HUNGER_MIN + (1 - sset.SPEED_HUNGER_MIN) * (a.hunger / sset.HUNGER_MAX)
            happy_mult = 1.0 + sset.SPEED_HAPPY_BONUS_MAX * (a.happiness / sset.HAPPINESS_MAX)
            vx_eff = s["vx"] * hunger_mult * happy_mult

            s["x"] += vx_eff * dt
            if s["x"] < left:
                s["x"] = left; s["vx"] = abs(s["vx"])
            elif s["x"] > right:
                s["x"] = right; s["vx"] = -abs(s["vx"])

            s["t"] += dt
            if s["t"] >= 0.15:
                s["frame"] = (s["frame"] + 1) % 4
                s["t"] = 0.0

        self._draw()

    def refresh(self):
        self._ensure_sprites()
        self._update_action_bar()
        self._draw()

    # ---------- drawing ----------
    def _compute_hab_zones(self, x0, y0, w, h, near_h):
        """Lay out simple drop slots just above the fence."""
        habs = self.services.sim.get_habitats()
        slots = max(1, len(habs))
        if slots == 0:
            self._hab_zones = []
            return
        pad = 12
        zone_w = (w - pad * (slots + 1)) / slots
        zone_h = max(36.0, h * 0.08)
        y = y0 + near_h + 8
        zones = []
        for i, hab in enumerate(habs):
            zx = x0 + pad + i * (zone_w + pad)
            zones.append({"id": hab.id, "name": hab.name, "rect": (zx, y, zone_w, zone_h)})
        self._hab_zones = zones

    def _draw(self):
        cb = self.canvas_box
        w, h = cb.size
        x0, y0 = cb.pos
        if w < 10 or h < 10:
            return

        sky_h = h * 0.65
        mid_h = h * 0.19
        near_h = h * 0.16

        # compute drop zones
        self._compute_hab_zones(x0, y0, w, h, near_h)

        cb.canvas.clear()
        with cb.canvas:
            # sky & dunes
            Color(0.60, 0.84, 1.0, 1.0); Rectangle(pos=(x0, y0 + h - sky_h), size=(w, sky_h))
            Color(0.55, 0.80, 0.98, 1.0); Rectangle(pos=(x0, y0 + h - sky_h * 0.55), size=(w, sky_h * 0.2))
            Color(0.53, 0.78, 0.96, 1.0); Rectangle(pos=(x0, y0 + h - sky_h * 0.80), size=(w, sky_h * 0.15))
            Color(0.86, 0.80, 0.58, 1.0); Rectangle(pos=(x0, y0 + near_h), size=(w, mid_h))
            Color(0.92, 0.84, 0.60, 1.0); Rectangle(pos=(x0, y0), size=(w, near_h))
            Color(0.35, 0.28, 0.18, 1.0); Line(points=[x0, y0 + near_h + 6, x0 + w, y0 + near_h + 6], width=1.3)

            # habitat drop zones
            for z in self._hab_zones:
                zx, zy, zw, zh = z["rect"]
                Color(0.18, 0.18, 0.18, 0.25); Rectangle(pos=(zx, zy), size=(zw, zh))
                Color(0.18, 0.18, 0.18, 1.0); Line(rectangle=(zx, zy, zw, zh), width=1.0)

            # sprites
            sset = self.services.settings
            scale = max(sset.PIXEL_SCALE_MIN, min(sset.PIXEL_SCALE_MAX, w / 160.0))
            spw, sph = 24 * scale, 16 * scale
            ground_y = y0 + near_h - 2

            for a in self.services.sim.get_armadillos()[:16]:
                s = self._sprites[a.id]
                tex = s["frames"][s["frame"]]
                width = spw if s["vx"] >= 0 else -spw
                px = s["x"] - (spw / 2 if s["vx"] >= 0 else -spw / 2)
                Rectangle(texture=tex, pos=(px, ground_y), size=(width, sph))
                s["rect"] = (px if width >= 0 else px + width, ground_y, abs(width), sph)

                if self.services.ui.selected_armadillo_id == a.id:
                    Color(0.22, 0.65, 0.38, 1.0)
                    Line(rectangle=(s["rect"][0]-2, s["rect"][1]-2, s["rect"][2]+4, s["rect"][3]+4), width=1.2)

            # drag ghost
            ui = self.services.ui
            if ui._drag_started and ui.dragging_id:
                Color(0.22, 0.65, 0.38, 0.5)
                cx, cy = ui.drag_pos
                Rectangle(pos=(cx - spw/2, ground_y + sph*0.2), size=(spw, sph))


# ---------------- Habitats ----------------

class HabitatScreen(BaseScreen):
    def __init__(self, services, **kwargs):
        super().__init__(services, **kwargs)
        self.box = BoxLayout(orientation="vertical", spacing=8, padding=12)
        self.info = Label(text="Habitats")
        self.box.add_widget(self.info)
        self.controls = BoxLayout(size_hint_y=None, height=56, spacing=8)
        self.add_btn = Button(text="Add Habitat (-100)")
        self.controls.add_widget(self.add_btn)
        self.box.add_widget(self.controls)
        self.add_widget(self.box)

        self.add_btn.bind(on_release=lambda *_: self._add_habitat())

    def on_pre_enter(self, *args): self.refresh()

    def refresh(self):
        arms = self.services.sim.get_armadillos()
        lines, habs = [], self.services.sim.get_habitats()
        for h in habs:
            occ = [a for a in arms if a.habitat_id == h.id]
            lines.append(f"{h.name} ({h.biome}) {len(occ)}/{h.capacity}")
        self.info.text = "\n".join(lines) if lines else "No habitats yet."

    def _add_habitat(self):
        if not self.services.econ.spend(self.services.settings.NEW_HABITAT_COST):
            self.info.text = "Not enough coins for new habitat."
            return
        h = Habitat.new_default(self.services.settings)
        habs = self.services.sim.get_habitats()
        habs.append(h)
        self.services.sim.set_habitats(habs)
        self.refresh()


# ---------------- Breeding ----------------

class BreedingScreen(BaseScreen):
    def __init__(self, services, **kwargs):
        super().__init__(services, **kwargs)
        self.box = BoxLayout(orientation="vertical", spacing=10, padding=12)
        self.lbl = Label(text="Breed adults into the incubator.")
        self.box.add_widget(self.lbl)
        self.btn = Button(text="Breed first M+F adults (start incubation)")
        self.box.add_widget(self.btn)

        # incubator list UI
        self.inc_list = BoxLayout(orientation="vertical", spacing=6)
        self.box.add_widget(self.inc_list)

        self.add_widget(self.box)
        self.btn.bind(on_release=lambda *_: self._breed())

        Clock.schedule_interval(lambda dt: self._refresh_incubator_ui(), 0.25)

    def on_pre_enter(self, *args): self.refresh()

    def refresh(self):
        arms = self.services.sim.get_armadillos()
        adults = [a for a in arms if a.stage == "adult"]
        self.lbl.text = f"Adults ready: {len(adults)}"
        self._refresh_incubator_ui()

    def _breed(self):
        arms = [a for a in self.services.sim.get_armadillos() if a.stage == "adult"]
        mom = next((x for x in arms if x.sex == "F"), None)
        dad = next((x for x in arms if x.sex == "M"), None)
        if not (mom and dad):
            self.lbl.text = "Need an adult M and F."
            return
        egg = Armadillo.breed(self.services.settings, mom, dad)
        self.services.sim.start_incubation(egg)
        self.lbl.text = f"Egg in incubator! Color {egg.hex_color}"
        self._refresh_incubator_ui()

    def _refresh_incubator_ui(self):
        self.inc_list.clear_widgets()
        inc = self.services.sim.state.get("incubator", [])
        if not inc:
            self.inc_list.add_widget(Label(text="Incubator: empty"))
            return
        tps = self.services.settings.TICKS_PER_SEC
        for idx, entry in enumerate(inc):
            row = BoxLayout(orientation="horizontal", spacing=8, size_hint_y=None, height=36)
            ticks = entry["ticks_left"]
            seconds = max(0, int(ticks / tps))
            pb = ProgressBar(max=self.services.settings.EGG_TICKS, value=self.services.settings.EGG_TICKS - ticks)
            row.add_widget(Label(text=f"Egg #{idx+1}"))
            row.add_widget(pb)
            row.add_widget(Label(text=f"{seconds}s"))
            btn = Button(text="Speed +5s (-2)")
            def make_cb(i):
                return lambda *_: self._speed_up(i)
            btn.bind(on_release=make_cb(idx))
            row.add_widget(btn)
            self.inc_list.add_widget(row)

    def _speed_up(self, idx: int):
        if not self.services.econ.spend(2):
            return
        self.services.sim.speed_up_incubator(idx, self.services.settings.TICKS_PER_SEC * 5)
        self._refresh_incubator_ui()


# ---------------- Dex & Shop ----------------

class DexScreen(BaseScreen):
    def __init__(self, services, **kwargs):
        super().__init__(services, **kwargs)
        self.box = BoxLayout(orientation="vertical", spacing=6, padding=12)
        self.lbl = Label(text="Dex/Collection")
        self.box.add_widget(self.lbl)
        self.add_widget(self.box)

    def on_pre_enter(self, *args): self.refresh()

    def refresh(self):
        arms = self.services.sim.get_armadillos()
        lines = []
        for a in arms[:20]:
            lines.append(f"{a.nickname} {a.stage} {a.sex} {a.hex_color} (H{int(a.hunger)}/Happy{int(a.happiness)})")
        self.lbl.text = "\n".join(lines) if lines else "No armadillos yet."


class ShopScreen(BaseScreen):
    def __init__(self, services, **kwargs):
        super().__init__(services, **kwargs)
        self.box = BoxLayout(orientation="vertical", spacing=12, padding=12)
        self.info = Label(text="Shop: basic items coming soon.\nTip: long-press on Farm to drag into a habitat slot.")
        self.box.add_widget(self.info)
        self.add_widget(self.box)

    def on_pre_enter(self, *args): self.refresh()

    def refresh(self): pass


class SettingsScreen(BaseScreen):
    def __init__(self, services, **kwargs):
        super().__init__(services, **kwargs)
        self.box = BoxLayout(orientation="vertical", spacing=6, padding=12)
        self.lbl = Label(text="Settings (demo)")
        self.box.add_widget(self.lbl)
        self.add_widget(self.box)

    def on_pre_enter(self, *args): self.refresh()

# ui/components.py
from __future__ import annotations

import time
from typing import Optional, List, Tuple

from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import StringProperty, NumericProperty, BooleanProperty, ObjectProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.core.window import Window

from services.state import GameState
from services.economy import Economy

# KivyMD fallback handling
HAS_MD = True
try:
    from kivymd.uix.snackbar import Snackbar
    from kivymd.uix.boxlayout import MDBoxLayout
    from kivymd.uix.button import MDIconButton, MDRaisedButton, MDFlatButton
    from kivymd.uix.card import MDCard
    from kivymd.uix.list import TwoLineAvatarIconListItem, ImageLeftWidget
    from kivymd.uix.label import MDLabel
    from kivymd.uix.toolbar import MDTopAppBar
    from kivymd.uix.screenmanager import MDScreenManager
    from kivymd.uix.screen import MDScreen
    from kivymd.uix.dialog import MDDialog
    from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
except Exception:
    HAS_MD = False
    Snackbar = None  # type: ignore
    from kivy.uix.boxlayout import BoxLayout as MDBoxLayout  # type: ignore
    from kivy.uix.button import Button as MDRaisedButton  # type: ignore
    from kivy.uix.button import Button as MDFlatButton  # type: ignore
    from kivy.uix.button import Button as MDIconButton  # type: ignore
    from kivy.uix.label import Label as MDLabel  # type: ignore
    from kivy.uix.widget import Widget as MDCard  # type: ignore
    from kivy.uix.screenmanager import ScreenManager as MDScreenManager  # type: ignore
    from kivy.uix.screenmanager import Screen as MDScreen  # type: ignore
    MDBottomNavigation = None  # type: ignore
    MDBottomNavigationItem = None  # type: ignore
    MDTopAppBar = None  # type: ignore
    TwoLineAvatarIconListItem = BoxLayout  # type: ignore
    ImageLeftWidget = Image  # type: ignore
    MDDialog = None  # type: ignore


def show_toast(text: str) -> None:
    if HAS_MD and Snackbar:
        Snackbar(text=text, duration=1).open()
    else:
        # Simple fallback: window title update flash
        Window.set_title(f"Armadillo Farmer • {text}")
        Clock.schedule_once(lambda dt: Window.set_title("Armadillo Farmer"), 1.2)


# ---- Top bar --------------------------------------------------------------

class TopBar(MDBoxLayout):
    app = ObjectProperty(None)
    coin_text = StringProperty("0")

    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.height = dp(56)
        self.orientation = "horizontal"
        self.padding = dp(8)
        if HAS_MD and MDTopAppBar:
            # Built in KV adds toolbar; here we only use this for fallback if needed.
            pass

    def update_coin_label(self, coins: int):
        self.coin_text = str(coins)


# ---- Screen Manager with bottom nav --------------------------------------

class MDCompatibleScreenManager(MDScreenManager):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._root_container = None
        self._bottom_nav = None

    def build_root_with_nav(self, topbar: TopBar):
        # Root layout constructed in kv; here we just return a container when KivyMD is missing
        if HAS_MD:
            from kivy.uix.boxlayout import BoxLayout
            root = BoxLayout(orientation="vertical")
            # The kv file will add toolbar via ids; we still attach our screen manager to nav container.
            # We embed a BottomNavigation with items; each item contains a dummy MDScreen child that swaps self.current.
            from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem
            bn = MDBottomNavigation()
            for item_id, text, icon in [
                ("home", "Home", "home"),
                ("habitats", "Habitats", "terrain"),
                ("breeding", "Breeding", "egg"),
                ("dex", "Dex", "view-grid"),
                ("shop", "Shop", "cart"),
            ]:
                it = MDBottomNavigationItem(name=item_id, text=text, icon=icon)
                # Click handler: switch screens
                def make_switch(nm):
                    def _cb(*_):
                        self.current = nm
                    return _cb
                # Add a tiny button to trigger switch even when content area tapped
                btn = MDRaisedButton(text=f"Go to {text}", size_hint=(None, None), height=dp(0), opacity=0)
                btn.bind(on_release=make_switch(item_id))
                it.add_widget(btn)
                bn.add_widget(it)
            def on_switch(inst, item):
                # item is nav item; switch to its name
                try:
                    self.current = item.name
                except Exception:
                    pass
            bn.bind(on_tab_switch=lambda *a: on_switch(*a))
            root.add_widget(topbar)
            root.add_widget(self)
            root.add_widget(bn)
            self._root_container = root
            self._bottom_nav = bn
            return root
        else:
            from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelHeader
            from kivy.uix.boxlayout import BoxLayout
            root = BoxLayout(orientation="vertical")
            root.add_widget(topbar)
            tp = TabbedPanel(do_default_tab=False, tab_height=dp(44))
            for nm, txt in [
                ("home", "Home"),
                ("habitats", "Habitats"),
                ("breeding", "Breeding"),
                ("dex", "Dex"),
                ("shop", "Shop"),
            ]:
                th = TabbedPanelHeader(text=txt)
                th.bind(on_release=lambda *_a, n=nm: setattr(self, "current", n))
                tp.add_widget(th)
            root.add_widget(self)
            root.add_widget(tp)
            self._root_container = root
            return root


# ---- Armadillo Card -------------------------------------------------------

class ArmadilloCard(MDCard):
    did = StringProperty("")
    name = StringProperty("")
    subtitle = StringProperty("")
    selected = BooleanProperty(False)

    def __init__(self, did: str, name: str, subtitle: str, **kwargs):
        super().__init__(**kwargs)
        self.did = did
        self.name = name
        self.subtitle = subtitle
        self.orientation = "vertical"
        self.padding = dp(8)
        self.radius = [dp(12)]
        self.size_hint_y = None
        self.height = dp(96)
        self._long_press_ev = None
        self._drag_widget = None
        self._down_pos = (0, 0)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._down_pos = touch.pos
            # schedule long-press
            self._long_press_ev = Clock.schedule_once(lambda dt: self._start_drag(touch), 0.35)
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self._long_press_ev and self._long_press_ev.is_triggered:
            # already started drag; delegate end in drag
            pass
        else:
            if self.collide_point(*touch.pos):
                # Select
                GameState.instance().select(self.did)
                show_toast(f"Selected: {self.name}")
        if self._long_press_ev:
            self._long_press_ev.cancel()
            self._long_press_ev = None
        return super().on_touch_up(touch)

    def _start_drag(self, touch):
        # Only drag if this is currently selected (as per acceptance)
        st = GameState.instance()
        if st.selected_id != self.did:
            return
        self._drag_widget = DragShadow(self.name)
        self.get_root_window().add_widget(self._drag_widget)
        self._drag_widget.center = touch.pos
        touch.grab(self)

    def on_touch_move(self, touch):
        if touch.grab_current is self and self._drag_widget:
            self._drag_widget.center = touch.pos
            # highlight habitats under cursor
            root = self.parent
            while root.parent:
                root = root.parent
            try:
                habitat_screen = root.ids.get("habitats_screen")
                if habitat_screen:
                    habitat_screen.highlight_dropzones(touch.pos, True)
            except Exception:
                pass
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if touch.grab_current is self and self._drag_widget:
            # Drop
            root = self.parent
            while root.parent:
                root = root.parent
            dropped = False
            try:
                habitat_screen = root.ids.get("habitats_screen")
                if habitat_screen:
                    dropped = habitat_screen.try_drop(touch.pos)
                    habitat_screen.highlight_dropzones(touch.pos, False)
            except Exception:
                pass
            if dropped:
                show_toast("Moved to habitat")
            self.get_root_window().remove_widget(self._drag_widget)
            self._drag_widget = None
            touch.ungrab(self)
        # cancel pending long press if any
        if self._long_press_ev:
            self._long_press_ev.cancel()
            self._long_press_ev = None
        return super().on_touch_up(touch)


class DragShadow(FloatLayout):
    def __init__(self, label: str, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (None, None)
        self.size = (dp(100), dp(50))
        self.opacity = 0.85
        self.add_widget(Label(text=label, size_hint=(1, 1)))


# ---- Screens --------------------------------------------------------------

class BaseScreen(MDScreen):
    app = ObjectProperty(None)

    def __init__(self, name: str, app, **kwargs):
        super().__init__(name=name, **kwargs)
        self.app = app

    def refresh(self):
        pass


class HomeScreen(BaseScreen):
    def refresh(self):
        # Update selected label, enable/disable buttons in kv via ids
        st = GameState.instance()
        sel = st.get_selected()
        lbl = self.ids.get("selected_label")
        feed_btn = self.ids.get("feed_btn")
        pet_btn = self.ids.get("pet_btn")
        inv_lbl = self.ids.get("inventory_label")
        if lbl:
            lbl.text = f"Selected: {sel.name if sel else 'None'}"
        if inv_lbl:
            inv_lbl.text = f"Food: {st.inventory.get('food',0)} • Toys: {st.inventory.get('toy',0)}"
        enable = bool(sel)
        if feed_btn:
            feed_btn.disabled = not enable
        if pet_btn:
            pet_btn.disabled = not enable
        # Rebuild list lazily (simple)
        lst = self.ids.get("home_list")
        if lst and len(lst.children) != len(st.armadillos):
            lst.clear_widgets()
            for a in st.armadillos:
                subtitle = f"{a.sex} • {a.color} • Hunger {a.hunger}% • Happy {a.happiness}%"
                card = ArmadilloCard(a.id, a.name, subtitle)
                lst.add_widget(card)

    def on_feed(self):
        if GameState.instance().feed_selected():
            show_toast("Fed!")
        else:
            show_toast("Need food. Buy in Shop.")

    def on_pet(self):
        if GameState.instance().pet_selected():
            show_toast("Pet!")
        else:
            show_toast("Select an armadillo first.")


class HabitatsScreen(BaseScreen):
    dropzones: List[Tuple[Widget, str]] = []

    def on_pre_enter(self, *args):
        self._collect_dropzones()

    def _collect_dropzones(self):
        self.dropzones = []
        for idx in (1, 2, 3):
            w = self.ids.get(f"hab_card_{idx}")
            hlist = GameState.instance().habitats
            if w and len(hlist) >= idx:
                self.dropzones.append((w, hlist[idx - 1].id))

    def highlight_dropzones(self, pos, active: bool):
        for w, _hid in self.dropzones:
            if w.collide_point(*pos):
                w.opacity = 1.0 if active else 0.95

    def try_drop(self, pos) -> bool:
        st = GameState.instance()
        for w, hid in self.dropzones:
            if w.collide_point(*pos):
                if st.move_selected_to_habitat(hid):
                    return True
        return False

    def refresh(self):
        # Update capacity / occupants
        st = GameState.instance()
        for idx in (1, 2, 3):
            cap = self.ids.get(f"hab_cap_{idx}")
            occ = self.ids.get(f"hab_occ_{idx}")
            if cap and occ and len(st.habitats) >= idx:
                h = st.habitats[idx - 1]
                cap.text = f"Lv {h.level} • Cap {len(h.occupants)}/{h.capacity}"
                occ.text = ", ".join([st.get_by_id(i).name for i in h.occupants if st.get_by_id(i)])

    def on_upgrade(self, hid_idx: int):
        st = GameState.instance()
        if len(st.habitats) >= hid_idx:
            hid = st.habitats[hid_idx - 1].id
            ok = st.upgrade_habitat(hid, Economy.COST_HABITAT_UPGRADE, Economy.UPGRADE_CAPACITY_DELTA)
            if ok:
                show_toast("Habitat upgraded!")
            else:
                show_toast("Not enough coins.")


class BreedingScreen(BaseScreen):
    dad_choice = StringProperty("")
    mom_choice = StringProperty("")
    countdown_text = StringProperty("")

    def refresh(self):
        st = GameState.instance()
        # Populate pickers display text
        dads = [a for a in st.adults() if a.sex == "M"]
        moms = [a for a in st.adults() if a.sex == "F"]
        self.ids.get("dad_spinner").values = [f"{a.name} ({a.id})" for a in dads]
        self.ids.get("mom_spinner").values = [f"{a.name} ({a.id})" for a in moms]
        # Queue list
        qbox = self.ids.get("queue_box")
        if qbox:
            qbox.clear_widgets()
            for job in st.breeding_queue:
                rem = job.remaining()
                lbl = MDLabel(text=f"Egg {job.id[-4:]} • {rem}s")
                qbox.add_widget(lbl)

    def on_start_breeding(self):
        st = GameState.instance()
        dad_id = self._parse_id(self.ids.get("dad_spinner").text)
        mom_id = self._parse_id(self.ids.get("mom_spinner").text)
        if not dad_id or not mom_id:
            show_toast("Pick a male and a female adult.")
            return
        duration = Economy.INCUBATION_MIN_S
        job = st.start_breeding(dad_id, mom_id, duration)
        if job:
            show_toast("Incubation started!")
        else:
            show_toast("Invalid pair.")

    @staticmethod
    def _parse_id(text: str) -> Optional[str]:
        if "(" in text and ")" in text:
            return text.split("(")[-1].strip(")")
        return None


class DexScreen(BaseScreen):
    def refresh(self):
        st = GameState.instance()
        grid = self.ids.get("dex_grid")
        if grid:
            grid.clear_widgets()
            for color in sorted(list(st.dex_colors)):
                grid.add_widget(MDLabel(text=color, halign="center"))


class ShopScreen(BaseScreen):
    def on_buy_food(self):
        ok = GameState.instance().buy("food", Economy.COST_FOOD)
        show_toast("Bought food!" if ok else "Not enough coins.")

    def on_buy_toy(self):
        ok = GameState.instance().buy("toy", Economy.COST_TOY)
        show_toast("Bought toy!" if ok else "Not enough coins.")

    def refresh(self):
        st = GameState.instance()
        inv = self.ids.get("shop_inv")
        if inv:
            inv.text = f"Food: {st.inventory.get('food',0)} • Toys: {st.inventory.get('toy',0)}"

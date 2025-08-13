from kivy.uix.screenmanager import Screen
from kivy.properties import ListProperty, NumericProperty, StringProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.app import App
from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle

from ..drag import DropZoneMixin
from ..widgets import ToastManager, Haptics, log_event
from ..constants import tr, ACCENT, CARD, BORDER


class ArmadilloWidget(Widget):
    """Visible square token representing an armadillo.

    - Draws a rounded square so it's tappable/visible.
    - Exposes drag_payload() so DragManager can pick it up on long-press.
    - On tap, selects this armadillo in the HomeScreen.
    """
    armadillo_id = StringProperty("")
    selected = BooleanProperty(False)

    def on_kv_post(self, *a):
        with self.canvas.before:
            # selection/back plate
            self._sel_color = Color(ACCENT[0], ACCENT[1], ACCENT[2], 0.22 if self.selected else 0.0)
            self._sel = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)] * 4)
            # body
            Color(1, 1, 1, 0.06)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)] * 4)
        self.bind(pos=self._sync, size=self._sync, selected=self._apply_selected)

    def _sync(self, *_):
        self._sel.pos = self.pos
        self._sel.size = self.size
        self._bg.pos = self.pos
        self._bg.size = self.size

    def _apply_selected(self, *_):
        self._sel_color.a = 0.22 if self.selected else 0.0

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            app = App.get_running_app()
            scr = app.root.sm.get_screen("home")
            scr.select(self.armadillo_id)
            return True
        return super().on_touch_down(touch)

    def drag_payload(self):
        return {"type": "armadillo", "id": self.armadillo_id}


class PenWidget(DropZoneMixin, BoxLayout):
    """A 2x4 grid that holds up to 8 armadillos."""
    pen_index = NumericProperty(0)
    name = StringProperty("Pen")

    def on_kv_post(self, *a):
        # Build the grid contents from state (no loops in KV)
        Clock.schedule_once(lambda dt: self.populate_grid(), 0)

    def populate_grid(self):
        app = App.get_running_app()
        ids_in_pen = [a['id'] for a in app.state.armadillos if a['pen'] == self.pen_index]
        grid = self.ids.get('grid')
        if not grid:
            return
        grid.clear_widgets()
        # add up to 8 tokens
        for a_id in ids_in_pen[:8]:
            grid.add_widget(
                ArmadilloWidget(
                    armadillo_id=a_id,
                    selected=(app.root.sm.get_screen("home").selected_id == a_id),
                    size_hint=(None, None),
                    size=(dp(56), dp(56)),
                )
            )
        # pad remaining cells so layout is stable
        for _ in range(max(0, 8 - len(ids_in_pen))):
            grid.add_widget(Widget(size_hint=(None, None), size=(dp(56), dp(56))))

    def accepts(self, payload: dict) -> bool:
        if not super().accepts(payload):
            return False
        app = App.get_running_app()
        return app.state.can_place(payload.get("id"), self.pen_index)

    def on_drop(self, payload: dict):
        app = App.get_running_app()
        if app.state.move_armadillo(payload.get("id"), self.pen_index):
            ToastManager.show(tr("Moved!"))
            app.autosave_later()
            log_event("armadillo_moved", pen=self.pen_index)
            # refresh all pens to update both source and destination
            app.root.sm.get_screen("home").refresh_all_pens()


class HomeScreen(Screen):
    pens = ListProperty([])
    selected_id = StringProperty("")
    armadillos = ListProperty([])

    def on_kv_post(self, *args):
        self.refresh_from_state()
        self._build_pens_strip()
        Clock.schedule_interval(lambda dt: self._tick(dt), 0.5)

    # ------------ UI helpers ------------
    def _tick(self, dt):
        pass

    def _get_selected_dict(self):
        if not self.selected_id:
            return None
        app = App.get_running_app()
        for a in app.state.armadillos:
            if a["id"] == self.selected_id:
                return a
        return None

    def _update_selected_hud(self):
        """Update the hunger/happiness bars + button disabled states."""
        a = self._get_selected_dict()
        bar_h = self.ids.get("bar_hunger")
        bar_p = self.ids.get("bar_happy")
        feed_btn = self.ids.get("btn_feed")
        pet_btn = self.ids.get("btn_pet")
        if not a:
            if bar_h: bar_h.value = 0
            if bar_p: bar_p.value = 0
            if feed_btn: feed_btn.disabled = True
            if pet_btn: pet_btn.disabled = True
            return
        # In this simple model, hunger 0 = full; we show "fullness" as 1 - hunger.
        if bar_h: bar_h.value = max(0.0, min(1.0, 1.0 - a.get("hunger", 0.0)))
        if bar_p: bar_p.value = max(0.0, min(1.0, a.get("happiness", 0.0)))
        if feed_btn: feed_btn.disabled = a.get("hunger", 0.0) <= 0.01
        if pet_btn: pet_btn.disabled = a.get("happiness", 0.0) >= 0.99

    # ------------ State sync ------------
    def refresh_from_state(self):
        app = App.get_running_app()
        self.armadillos = app.state.armadillos
        self.pens = app.state.pens

    def _build_pens_strip(self):
        app = App.get_running_app()
        strip = self.ids.get("pens_strip")
        if not strip:
            return
        strip.clear_widgets()
        for i, p in enumerate(app.state.pens):
            strip.add_widget(PenWidget(pen_index=i, name=p.get("name", f"Pen {i+1}")))

    def refresh_all_pens(self):
        strip = self.ids.get("pens_strip")
        if not strip:
            return
        for child in strip.children:
            if isinstance(child, PenWidget):
                child.populate_grid()

    # ------------ Actions ------------
    def select(self, armadillo_id: str):
        self.selected_id = armadillo_id
        # Mark tokens visually
        strip = self.ids.get("pens_strip")
        if strip:
            for child in strip.children:
                if isinstance(child, PenWidget):
                    grid = child.ids.get("grid")
                    if grid:
                        for token in grid.children:
                            if isinstance(token, ArmadilloWidget):
                                token.selected = (token.armadillo_id == armadillo_id)
        self._update_selected_hud()

    def feed_selected(self):
        if not self.selected_id:
            ToastManager.show(tr("Pick an armadillo first"))
            return
        app = App.get_running_app()
        if app.state.feed(self.selected_id):
            ToastManager.show(tr("Munch munch!"))
            Haptics.tap()
            app.autosave_later()
            self._update_selected_hud()

    def pet_selected(self):
        if not self.selected_id:
            ToastManager.show(tr("Pick an armadillo first"))
            return
        app = App.get_running_app()
        if app.state.pet(self.selected_id):
            ToastManager.show(tr("Happy!"))
            Haptics.tap()
            app.autosave_later()
            self._update_selected_hud()

from kivy.uix.screenmanager import Screen
from kivy.properties import ListProperty, NumericProperty, StringProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.app import App
from kivy.metrics import dp

from ..drag import DropZoneMixin
from ..widgets import ToastManager, Haptics, log_event
from ..constants import tr

class ArmadilloWidget(Widget):
    armadillo_id = StringProperty("")
    selected = BooleanProperty(False)
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            app = App.get_running_app()
            scr = app.root.sm.get_screen("home")
            scr.select(self.armadillo_id)
        return super().on_touch_down(touch)
    def drag_payload(self):
        return {"type": "armadillo", "id": self.armadillo_id}

class PenWidget(DropZoneMixin, BoxLayout):
    pen_index = NumericProperty(0)
    name = StringProperty("Pen")
    def on_kv_post(self, *a):
        Clock.schedule_once(lambda dt: self.populate_grid(), 0)
    def populate_grid(self):
        app = App.get_running_app()
        ids_in_pen = [a['id'] for a in app.state.armadillos if a['pen'] == self.pen_index]
        grid = self.ids.get('grid')
        if not grid: return
        grid.clear_widgets()
        for a_id in ids_in_pen[:8]:
            grid.add_widget(ArmadilloWidget(armadillo_id=a_id, size_hint=(None, None), size=(dp(48), dp(48))))
        for _ in range(max(0, 8 - len(ids_in_pen))):
            grid.add_widget(Widget(size_hint=(None, None), size=(dp(48), dp(48))))
    def accepts(self, payload: dict) -> bool:
        if not super().accepts(payload): return False
        app = App.get_running_app()
        return app.state.can_place(payload.get("id"), self.pen_index)
    def on_drop(self, payload: dict):
        app = App.get_running_app()
        if app.state.move_armadillo(payload.get("id"), self.pen_index):
            ToastManager.show(tr("Moved!"))
            app.autosave_later()
            log_event("armadillo_moved", pen=self.pen_index)
            app.root.sm.get_screen("home").refresh_all_pens()

class HomeScreen(Screen):
    pens = ListProperty([])
    selected_id = StringProperty("")
    armadillos = ListProperty([])
    def on_kv_post(self, *args):
        self.refresh_from_state()
        self._build_pens_strip()
        Clock.schedule_interval(lambda dt: self._tick(dt), 0.5)
    def _tick(self, dt): pass
    def refresh_from_state(self):
        app = App.get_running_app()
        self.armadillos = app.state.armadillos
        self.pens = app.state.pens
    def _build_pens_strip(self):
        app = App.get_running_app()
        strip = self.ids.get("pens_strip")
        if not strip: return
        strip.clear_widgets()
        for i, p in enumerate(app.state.pens):
            strip.add_widget(PenWidget(pen_index=i, name=p.get("name", f"Pen {i+1}")))
    def refresh_all_pens(self):
        strip = self.ids.get("pens_strip")
        if not strip: return
        for child in strip.children:
            if isinstance(child, PenWidget):
                child.populate_grid()
    def select(self, armadillo_id: str):
        self.selected_id = armadillo_id
    def feed_selected(self):
        if not self.selected_id:
            ToastManager.show(tr("Pick an armadillo first")); return
        app = App.get_running_app()
        if app.state.feed(self.selected_id):
            ToastManager.show(tr("Munch munch!")); Haptics.tap(); app.autosave_later()
    def pet_selected(self):
        if not self.selected_id:
            ToastManager.show(tr("Pick an armadillo first")); return
        app = App.get_running_app()
        if app.state.pet(self.selected_id):
            ToastManager.show(tr("Happy!")); Haptics.tap(); app.autosave_later()

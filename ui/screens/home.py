# ui/screens/home.py
from kivy.uix.screenmanager import Screen
from kivy.properties import ListProperty, ObjectProperty, NumericProperty, StringProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scatterlayout import ScatterLayout
from kivy.uix.widget import Widget
from kivy.clock import Clock

from ..drag import DropZoneMixin
from ..widgets import ToastManager, Haptics, log_event
from ..constants import tr, ACCENT, DANGER

class ArmadilloWidget(Widget):
    """Simple square token representing an armadillo."""
    armadillo_id = StringProperty("")
    selected = BooleanProperty(False)

    def drag_payload(self):
        return {"type": "armadillo", "id": self.armadillo_id}

class PenWidget(DropZoneMixin, BoxLayout):
    pen_index = NumericProperty(0)
    name = StringProperty("Pen")

    def accepts(self, payload: dict) -> bool:
        if not super().accepts(payload):
            return False
        app = self.get_app()
        return app.state.can_place(payload.get("id"), self.pen_index)

    def on_drop(self, payload: dict):
        app = self.get_app()
        if app.state.move_armadillo(payload.get("id"), self.pen_index):
            ToastManager.show(tr("Moved!"))
            app.autosave_later()
            log_event("armadillo_moved", pen=self.pen_index)

    def get_app(self):
        from kivy.app import App
        return App.get_running_app()

class HomeScreen(Screen):
    pens = ListProperty([])
    selected_id = StringProperty("")
    armadillos = ListProperty([])

    def on_kv_post(self, *args):
        self.refresh_from_state()
        Clock.schedule_interval(lambda dt: self._tick(dt), 1/2)

    def _tick(self, dt):
        # keep bars fresh, etc.
        pass

    def refresh_from_state(self):
        app = self.get_app()
        self.armadillos = app.state.armadillos
        self.pens = app.state.pens

    def select(self, armadillo_id: str):
        self.selected_id = armadillo_id

    def feed_selected(self):
        app = self.get_app()
        if app.state.feed(self.selected_id):
            ToastManager.show(tr("Munch munch!"))
            Haptics.tap()
            app.autosave_later()

    def pet_selected(self):
        app = self.get_app()
        if app.state.pet(self.selected_id):
            ToastManager.show(tr("Happy!"))
            Haptics.tap()
            app.autosave_later()

    def get_app(self):
        from kivy.app import App
        return App.get_running_app()

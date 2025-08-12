from kivy.uix.screenmanager import Screen
from kivy.properties import StringProperty, ListProperty, NumericProperty
from kivy.clock import Clock
from kivy.app import App

from ..drag import DropZoneMixin
from ..widgets import ToastManager, Dialog, log_event
from ..constants import tr

class ParentSlot(DropZoneMixin):
    slot = NumericProperty(0)
    armadillo_id = StringProperty("")
    def accepts(self, payload: dict) -> bool:
        return payload.get("type") == "armadillo"
    def on_drop(self, payload: dict):
        self.armadillo_id = payload.get("id")
        ToastManager.show(tr("Parent set"))

class BreedingScreen(Screen):
    parent_a = StringProperty("")
    parent_b = StringProperty("")
    queue = ListProperty([])
    def on_kv_post(self, *a):
        Clock.schedule_interval(self._tick, 1.0)
        self.refresh()
    def _tick(self, dt):
        app = App.get_running_app()
        changed = app.state.advance_incubators(1.0)
        if changed:
            self.refresh(); app.autosave_later()
    def start(self):
        app = App.get_running_app()
        if not self.parent_a or not self.parent_b:
            ToastManager.show(tr("Choose two parents")); return
        if app.state.start_breed(self.parent_a, self.parent_b):
            ToastManager.show(tr("Breeding started")); log_event("breed_started")
            self.refresh(); app.autosave_later()
    def speed_up(self, idx):
        app = App.get_running_app()
        app.state.speed_up_incubator(idx, seconds=10); self.refresh()
    def refresh(self):
        app = App.get_running_app(); self.queue = app.state.incubator

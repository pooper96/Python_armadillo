# ui/screens/habitats.py
from kivy.uix.screenmanager import Screen
from kivy.properties import ListProperty, ObjectProperty, NumericProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout

from ..drag import DropZoneMixin
from ..widgets import Dialog, ToastManager, log_event
from ..constants import tr

class HabitatCard(DropZoneMixin, BoxLayout):
    idx = NumericProperty(0)
    name = StringProperty("")
    capacity = NumericProperty(0)
    yield_mod = NumericProperty(0.0)
    biome = StringProperty("")

    def accepts(self, payload: dict) -> bool:
        if payload.get("type") != "armadillo":
            return False
        app = self.get_app()
        return app.state.can_place(payload.get("id"), self.idx)

    def on_drop(self, payload: dict):
        app = self.get_app()
        if app.state.move_armadillo(payload.get("id"), self.idx):
            ToastManager.show(tr("Assigned to habitat"))
            app.autosave_later()
            log_event("armadillo_assigned", habitat=self.idx)

    def upgrade(self):
        app = self.get_app()
        h = app.state.pens[self.idx]
        d = Dialog(title=tr("Upgrade habitat?"),
                   message=tr(f"Increase capacity of {h['name']} (+1). Cost: 20 coins"),
                   on_confirm=lambda *_: self._do_upgrade())
        d.open()

    def _do_upgrade(self):
        app = self.get_app()
        if app.state.upgrade_habitat(self.idx):
            ToastManager.show(tr("Upgraded!"))
            app.autosave_later()
            log_event("habitat_upgraded", idx=self.idx)

    def get_app(self):
        from kivy.app import App
        return App.get_running_app()

class HabitatsScreen(Screen):
    habitats = ListProperty([])

    def on_kv_post(self, *a):
        self.refresh()

    def refresh(self):
        app = self.get_app()
        self.habitats = app.state.pens

    def get_app(self):
        from kivy.app import App
        return App.get_running_app()

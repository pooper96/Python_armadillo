# ui/screens/settings.py
from kivy.uix.screenmanager import Screen
from kivy.properties import BooleanProperty, StringProperty
from kivy.clock import Clock
import json
import os

from ..widgets import ToastManager
from ..constants import tr

class SettingsScreen(Screen):
    music = BooleanProperty(True)
    sfx = BooleanProperty(True)
    haptics = BooleanProperty(True)
    reduce_motion = BooleanProperty(False)
    large_text = BooleanProperty(False)
    version = StringProperty("1.0.0")

    def on_kv_post(self, *a):
        app = self.get_app()
        self.music = app.music
        self.sfx = app.sfx
        self.haptics = app.haptics
        self.reduce_motion = app.reduce_motion
        self.large_text = app.large_text

    def apply(self):
        app = self.get_app()
        app.music = self.music
        app.sfx = self.sfx
        app.haptics = self.haptics
        app.reduce_motion = self.reduce_motion
        app.large_text = self.large_text
        ToastManager.show(tr("Settings updated"))

    def backup(self):
        app = self.get_app()
        path = os.path.join(app.user_data_dir, "save_backup.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(app.state.to_dict(), f, ensure_ascii=False, indent=2)
        ToastManager.show(tr("Backup saved"))

    def restore(self):
        app = self.get_app()
        path = os.path.join(app.user_data_dir, "save_backup.json")
        if not os.path.exists(path):
            ToastManager.show(tr("No backup found"))
            return
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        app.state.from_dict(data)
        app.autosave_later()
        ToastManager.show(tr("Restore complete"))

    def reset_game(self):
        app = self.get_app()
        app.state.reset()
        app.autosave_later()
        ToastManager.show(tr("Game reset"))

    def get_app(self):
        from kivy.app import App
        return App.get_running_app()

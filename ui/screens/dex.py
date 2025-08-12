# ui/screens/dex.py
from kivy.uix.screenmanager import Screen
from kivy.properties import ListProperty, DictProperty, StringProperty
from ..widgets import Dialog
from ..constants import tr

class DexScreen(Screen):
    items = ListProperty([])

    def on_kv_post(self, *a):
        self.refresh()

    def refresh(self):
        app = self.get_app()
        self.items = app.state.dex_items

    def open_detail(self, item):
        Dialog(title=tr(item.get("name", "Armadillo")),
               message=tr(f"Rarity: {item.get('rarity','?')}\nBiome: {item.get('biome','?')}"),
               on_confirm=lambda *_: None).open()

    def get_app(self):
        from kivy.app import App
        return App.get_running_app()

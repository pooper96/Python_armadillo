from kivy.uix.screenmanager import Screen
from kivy.properties import ListProperty, StringProperty
from ..widgets import Dialog, ToastManager, log_event
from ..constants import tr

class ShopScreen(Screen):
    tab = StringProperty("packs")
    packs = ListProperty([])
    upgrades = ListProperty([])
    def on_kv_post(self, *a):
        self.packs = [
            {"name": "Small Coin Pack", "price": "Free (stub)", "delta": 50},
            {"name": "Big Coin Pack", "price": "Free (stub)", "delta": 150},
        ]
        self.upgrades = [
            {"name": "Extra Incubator Slot", "desc": "Breed more at once", "cost": 100, "key": "inc_slot"},
        ]
    def buy_pack(self, idx):
        p = self.packs[idx]
        def do():
            app = self.get_app()
            app.state.add_coins(p["delta"])
            ToastManager.show(tr("Purchase complete"))
            log_event("iap_stub", item=p["name"])
            app.autosave_later()
        Dialog(title=tr("Confirm purchase"),
               message=tr(f"{p['name']} → {p['price']}"),
               on_confirm=lambda *_: do()).open()
    def buy_upgrade(self, idx):
        u = self.upgrades[idx]
        def do():
            app = self.get_app()
            if app.state.spend_coins(u["cost"]):
                if u["key"] == "inc_slot": app.state.inc_slots += 1
                ToastManager.show(tr("Upgrade purchased"))
                log_event("upgrade_bought", key=u["key"])
                app.autosave_later()
            else:
                ToastManager.show(tr("Not enough coins"))
        Dialog(title=tr("Confirm upgrade"),
               message=tr(f"{u['name']} – {u['desc']} (Cost {u['cost']})"),
               on_confirm=lambda *_: do()).open()
    def get_app(self):
        from kivy.app import App
        return App.get_running_app()

from kivy.config import Config

# Desktop/mobile friendly defaults BEFORE any Kivy window is created
Config.set('graphics', 'multisamples', '0')
Config.set('kivy', 'log_enable', '1')
Config.set('kivy', 'keyboard_mode', 'systemanddock')
# Stop the red multitouch circles on desktop
Config.set('input', 'mouse', 'mouse,disable_multitouch')

from kivy.app import App
from kivy.core.window import Window
Window.softinput_mode = "pan"

from kivy.uix.boxlayout import BoxLayout
from kivy.uix.screenmanager import ScreenManager
from kivy.clock import Clock

from settings import Settings
from services.save import SaveService
from services.sim import SimService
from services.economy import EconomyService
from models.habitat import Habitat
from models.armadillo import Armadillo
from models.genetics import RNG
from ui.screens import HomeScreen, HabitatScreen, BreedingScreen, DexScreen, ShopScreen, SettingsScreen
from ui.widgets import TopBar
from assets.procedural import ProceduralAssets


class ServiceContainer:
    def __init__(self, settings: Settings, save: SaveService, sim: SimService, econ: EconomyService, assets: ProceduralAssets):
        self.settings = settings
        self.save = save
        self.sim = sim
        self.econ = econ
        self.assets = assets


class Root(BoxLayout):
    """Persistent TopBar + ScreenManager so the nav always works."""
    def __init__(self, services, **kw):
        super().__init__(orientation="vertical", **kw)
        self.services = services
        self.topbar = TopBar(services)
        self.add_widget(self.topbar)
        self.sm = ScreenManager()
        self.add_widget(self.sm)

        # Wire nav once
        self.topbar.home_btn.bind(on_release=lambda *_: self.switch("home"))
        self.topbar.hab_btn.bind(on_release=lambda *_: self.switch("habitat"))
        self.topbar.breed_btn.bind(on_release=lambda *_: self.switch("breeding"))
        self.topbar.dex_btn.bind(on_release=lambda *_: self.switch("dex"))
        self.topbar.shop_btn.bind(on_release=lambda *_: self.switch("shop"))
        self.topbar.settings_btn.bind(on_release=lambda *_: self.switch("settings"))

    def switch(self, name):
        self.sm.current = name
        self.topbar.set_active(name)


class ArmadilloFarmerApp(App):
    def build(self):
        self.title = "Armadillo Farmer"
        self.settings = Settings()
        self.save_service = SaveService(self.settings)
        self.assets = ProceduralAssets(self.settings)

        # Load or initialize state (includes RNG seed)
        state = self.save_service.load_or_init()
        RNG.set_seed(state["rng_seed"])

        # Economy / Sim services
        self.econ_service = EconomyService(self.settings, state)
        self.sim_service = SimService(self.settings, state, self.econ_service, self.save_service)
        self.services = ServiceContainer(self.settings, self.save_service, self.sim_service, self.econ_service, self.assets)

        # --- self-heal bootstrap so game is playable immediately ---
        if not state["habitats"]:
            h = Habitat.new_default(self.settings)
            state["habitats"].append(h.to_dict())
        else:
            h = Habitat.from_dict(state["habitats"][0])
        if len(state["armadillos"]) < 2:
            a1 = Armadillo.new_starter(self.settings, nickname="Sandy")
            a2 = Armadillo.new_starter(self.settings, nickname="Pebble")
            state["armadillos"].extend([a1.to_dict(), a2.to_dict()])
        # put first two in the pen as adults
        arms = [Armadillo.from_dict(d) for d in state["armadillos"]]
        for i, a in enumerate(arms[:2]):
            a.stage = "adult"
            a.habitat_id = h.id
            arms[i] = a
        state["armadillos"] = [a.to_dict() for a in arms]
        self.save_service.atomic_save_if_dirty(state)
        # ------------------------------------------------------------

        # Build persistent root
        self.root_widget = Root(self.services)
        sm = self.root_widget.sm
        sm.add_widget(HomeScreen(name="home", services=self.services))
        sm.add_widget(HabitatScreen(name="habitat", services=self.services))
        sm.add_widget(BreedingScreen(name="breeding", services=self.services))
        sm.add_widget(DexScreen(name="dex", services=self.services))
        sm.add_widget(ShopScreen(name="shop", services=self.services))
        sm.add_widget(SettingsScreen(name="settings", services=self.services))
        self.root_widget.switch("home")

        # Sim + autosave
        Clock.schedule_interval(self.sim_service.tick, 1.0 / self.settings.TICKS_PER_SEC)
        Clock.schedule_interval(lambda dt: self.save_service.atomic_save_if_dirty(self.sim_service.state),
                                self.settings.AUTOSAVE_INTERVAL_SEC)
        return self.root_widget


if __name__ == "__main__":
    ArmadilloFarmerApp().run()

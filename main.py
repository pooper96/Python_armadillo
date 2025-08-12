from kivy.config import Config
Config.set('graphics', 'multisamples', '0')
Config.set('kivy', 'log_enable', '1')
Config.set('kivy', 'keyboard_mode', 'systemanddock')
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
from services.ui_state import UIState
from models.habitat import Habitat
from models.armadillo import Armadillo
from models.genetics import RNG
from ui.screens import HomeScreen, HabitatScreen, BreedingScreen, DexScreen, ShopScreen, SettingsScreen
from ui.widgets import TopBar
from assets.procedural import ProceduralAssets


class ServiceContainer:
    def __init__(self, settings: Settings, save: SaveService, sim: SimService, econ: EconomyService, assets: ProceduralAssets, ui: UIState):
        self.settings = settings
        self.save = save
        self.sim = sim
        self.econ = econ
        self.assets = assets
        self.ui = ui


class Root(BoxLayout):
    def __init__(self, services, **kw):
        super().__init__(orientation="vertical", **kw)
        self.services = services
        self.topbar = TopBar(services)
        self.add_widget(self.topbar)
        self.sm = ScreenManager()
        self.add_widget(self.sm)
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
        settings = Settings()
        save_service = SaveService(settings)
        assets = ProceduralAssets(settings)
        state = save_service.load_or_init()
        RNG.set_seed(state["rng_seed"])

        econ_service = EconomyService(settings, state)
        sim_service = SimService(settings, state, econ_service, save_service)
        ui_state = UIState()
        services = ServiceContainer(settings, save_service, sim_service, econ_service, assets, ui_state)

        # Bootstrap / self-heal
        if not state["habitats"]:
            h = Habitat.new_default(settings)
            state["habitats"].append(h.to_dict())
        else:
            h = Habitat.from_dict(state["habitats"][0])

        if len(state["armadillos"]) < 2:
            a1 = Armadillo.new_starter(settings, nickname="Sandy")
            a2 = Armadillo.new_starter(settings, nickname="Pebble")
            # force sexes to differ for easy breeding
            if a1.sex == a2.sex:
                a2.sex = "M" if a1.sex == "F" else "F"
            state["armadillos"].extend([a1.to_dict(), a2.to_dict()])

        arms = [Armadillo.from_dict(d) for d in state["armadillos"]]
        for i, a in enumerate(arms[:2]):
            a.stage = "adult"
            a.habitat_id = h.id
            arms[i] = a
        state["armadillos"] = [a.to_dict() for a in arms]
        save_service.atomic_save_if_dirty(state)

        # Root + screens
        root = Root(services)
        sm = root.sm
        sm.add_widget(HomeScreen(name="home", services=services))
        sm.add_widget(HabitatScreen(name="habitat", services=services))
        sm.add_widget(BreedingScreen(name="breeding", services=services))
        sm.add_widget(DexScreen(name="dex", services=services))
        sm.add_widget(ShopScreen(name="shop", services=services))
        sm.add_widget(SettingsScreen(name="settings", services=services))
        root.switch("home")

        # Sim + autosave
        Clock.schedule_interval(sim_service.tick, 1.0 / settings.TICKS_PER_SEC)
        Clock.schedule_interval(lambda dt: save_service.atomic_save_if_dirty(sim_service.state),
                                settings.AUTOSAVE_INTERVAL_SEC)
        return root


if __name__ == "__main__":
    ArmadilloFarmerApp().run()

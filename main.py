from kivy.config import Config
Config.set('graphics', 'multisamples', '0')
Config.set('kivy', 'log_enable', '1')
Config.set('kivy', 'keyboard_mode', 'systemanddock')

from kivy.app import App
from kivy.core.window import Window
Window.softinput_mode = "pan"

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
from assets.procedural import ProceduralAssets


class ServiceContainer:
    def __init__(self, settings: Settings, save: SaveService, sim: SimService, econ: EconomyService, assets: ProceduralAssets):
        self.settings = settings
        self.save = save
        self.sim = sim
        self.econ = econ
        self.assets = assets


class ArmadilloFarmerApp(App):
    def build(self):
        self.title = "Armadillo Farmer"
        self.settings = Settings()
        self.save_service = SaveService(self.settings)
        self.assets = ProceduralAssets(self.settings)

        state = self.save_service.load_or_init()
        RNG.set_seed(state["rng_seed"])

        self.econ_service = EconomyService(self.settings, state)
        self.sim_service = SimService(self.settings, state, self.econ_service, self.save_service)
        self.services = ServiceContainer(self.settings, self.save_service, self.sim_service, self.econ_service, self.assets)

        # --- DEMO BOOTSTRAP / SELF-HEAL ---
        # Create a starter habitat and two adults placed inside it, if missing.
        if not state["habitats"]:
            h = Habitat.new_default(self.settings)
            state["habitats"].append(h.to_dict())
        else:
            h = Habitat.from_dict(state["habitats"][0])

        if len(state["armadillos"]) < 2:
            a1 = Armadillo.new_starter(self.settings, nickname="Sandy")
            a2 = Armadillo.new_starter(self.settings, nickname="Pebble")
            state["armadillos"].extend([a1.to_dict(), a2.to_dict()])

        # ensure first two are adults in the habitat so gameplay works immediately
        from models.armadillo import Armadillo as A
        arms = [A.from_dict(d) for d in state["armadillos"]]
        for i, a in enumerate(arms[:2]):
            a.stage = "adult"
            a.habitat_id = h.id
            arms[i] = a
        state["armadillos"] = [a.to_dict() for a in arms]
        self.save_service.atomic_save_if_dirty(state)
        # --- end bootstrap ---

        sm = ScreenManager()
        sm.add_widget(HomeScreen(name="home", services=self.services))
        sm.add_widget(HabitatScreen(name="habitat", services=self.services))
        sm.add_widget(BreedingScreen(name="breeding", services=self.services))
        sm.add_widget(DexScreen(name="dex", services=self.services))
        sm.add_widget(ShopScreen(name="shop", services=self.services))
        sm.add_widget(SettingsScreen(name="settings", services=self.services))

        Clock.schedule_interval(self.sim_service.tick, 1.0 / self.settings.TICKS_PER_SEC)
        Clock.schedule_interval(lambda dt: self.save_service.atomic_save_if_dirty(self.sim_service.state),
                                self.settings.AUTOSAVE_INTERVAL_SEC)
        return sm


if __name__ == "__main__":
    ArmadilloFarmerApp().run()

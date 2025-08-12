from kivy.config import Config

# Mobile-friendly defaults before any Kivy import that creates a window
Config.set('graphics', 'multisamples', '0')
Config.set('kivy', 'log_enable', '1')

from kivy.app import App
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
    """Explicit DI container passed to screens/services."""
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

        # Load or initialize state (includes RNG seed)
        state = self.save_service.load_or_init()

        # Initialize RNG with persisted seed for determinism
        RNG.set_seed(state["rng_seed"])

        # Economy / Sim services
        self.econ_service = EconomyService(self.settings, state)
        self.sim_service = SimService(self.settings, state, self.econ_service, self.save_service)

        # DI
        self.services = ServiceContainer(self.settings, self.save_service, self.sim_service, self.econ_service, self.assets)

        # Basic bootstrap if fresh save
        if not state["habitats"]:
            # Create starter habitat and two starters
            h = Habitat.new_default(self.settings)
            state["habitats"].append(h.to_dict())
            a1 = Armadillo.new_starter(self.settings, nickname="Sandy")
            a2 = Armadillo.new_starter(self.settings, nickname="Pebble")
            state["armadillos"].extend([a1.to_dict(), a2.to_dict()])
            self.save_service.atomic_save(state)

        # Screen manager
        sm = ScreenManager()
        sm.add_widget(HomeScreen(name="home", services=self.services))
        sm.add_widget(HabitatScreen(name="habitat", services=self.services))
        sm.add_widget(BreedingScreen(name="breeding", services=self.services))
        sm.add_widget(DexScreen(name="dex", services=self.services))
        sm.add_widget(ShopScreen(name="shop", services=self.services))
        sm.add_widget(SettingsScreen(name="settings", services=self.services))

        # Start non-blocking tick loop
        Clock.schedule_interval(self.sim_service.tick, 1.0 / self.settings.TICKS_PER_SEC)
        # Periodic autosave
        Clock.schedule_interval(lambda dt: self.save_service.atomic_save(self.sim_service.state), self.settings.AUTOSAVE_INTERVAL_SEC)

        return sm


if __name__ == "__main__":
    ArmadilloFarmerApp().run()

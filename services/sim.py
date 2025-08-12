from typing import Dict, List
from settings import Settings
from models.armadillo import Armadillo
from models.habitat import Habitat


class SimService:
    def __init__(self, settings: Settings, state: Dict, econ, save):
        self.settings = settings
        self.state = state
        self.econ = econ
        self.save = save
        self._payout_counter = 0

    # -------- state helpers --------
    def get_armadillos(self) -> List[Armadillo]:
        return [Armadillo.from_dict(d) for d in self.state["armadillos"]]

    def set_armadillos(self, lst: List[Armadillo]):
        self.state["armadillos"] = [a.to_dict() for a in lst]

    def get_habitats(self) -> List[Habitat]:
        return [Habitat.from_dict(d) for d in self.state["habitats"]]

    def set_habitats(self, lst: List[Habitat]):
        self.state["habitats"] = [h.to_dict() for h in lst]

    # -------- game logic --------
    def advance_age_and_stage(self, a: Armadillo):
        a.age_ticks += 1
        if a.stage == "egg" and a.age_ticks >= self.settings.EGG_TICKS:
            a.stage = "juvenile"
            a.nickname = "Hatchling"
        elif a.stage == "juvenile" and a.age_ticks >= self.settings.JUVENILE_TICKS:
            a.stage = "adult"
        elif a.stage == "adult" and a.age_ticks >= self.settings.RETIRE_AGE_TICKS:
            a.stage = "retired"

    def mood_decay_tick(self, a: Armadillo):
        if a.stage != "egg":
            a.hunger = max(0, min(self.settings.HUNGER_MAX, a.hunger - self.settings.HUNGER_DECAY_PER_TICK))
            a.happiness = max(0, min(self.settings.HAPPINESS_MAX, a.happiness - self.settings.HAPPINESS_DECAY_PER_TICK))

    def habitat_income_tick(self):
        total = 0.0
        for a in self.get_armadillos():
            if a.habitat_id and a.stage in ("adult", "retired"):
                rarity_weight = (1.0 + a.rarity * self.settings.RARITY_YIELD_MULTIPLIER)
                hunger_mult = self.settings.HUNGER_INCOME_MIN_MULT + \
                              (1 - self.settings.HUNGER_INCOME_MIN_MULT) * (a.hunger / self.settings.HUNGER_MAX)
                happy_mult = 1.0 + self.settings.HAPPINESS_INCOME_BONUS_MAX * (a.happiness / self.settings.HAPPINESS_MAX)
                total += self.settings.HABITAT_BASE_YIELD_PER_TICK * rarity_weight * hunger_mult * happy_mult
        if total > 0:
            self.econ.add_coins(total)

    # -------- incubator --------
    def start_incubation(self, egg: Armadillo):
        self.state.setdefault("incubator", [])
        self.state["incubator"].append({
            "child": egg.to_dict(),
            "ticks_left": self.settings.EGG_TICKS
        })

    def process_incubator(self):
        remaining = []
        for entry in self.state.get("incubator", []):
            entry["ticks_left"] -= 1
            if entry["ticks_left"] <= 0:
                child = Armadillo.from_dict(entry["child"])
                child.stage = "juvenile"
                child.age_ticks = 0
                self.state["armadillos"].append(child.to_dict())
            else:
                remaining.append(entry)
        self.state["incubator"] = remaining

    def speed_up_incubator(self, idx: int, ticks: int):
        inc = self.state.setdefault("incubator", [])
        if 0 <= idx < len(inc):
            inc[idx]["ticks_left"] = max(0, inc[idx]["ticks_left"] - ticks)

    # -------- main tick --------
    def tick(self, dt):
        self.state["tick"] += 1
        arms = self.get_armadillos()
        for a in arms:
            self.advance_age_and_stage(a)
            self.mood_decay_tick(a)
        self.set_armadillos(arms)

        self.habitat_income_tick()
        self.process_incubator()

        self._payout_counter += 1
        if self._payout_counter >= self.settings.ECON_PAYOUT_INTERVAL_TICKS:
            self._payout_counter = 0

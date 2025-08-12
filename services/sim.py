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

    def get_armadillos(self) -> List[Armadillo]:
        return [Armadillo.from_dict(d) for d in self.state["armadillos"]]

    def set_armadillos(self, lst: List[Armadillo]):
        self.state["armadillos"] = [a.to_dict() for a in lst]

    def get_habitats(self) -> List[Habitat]:
        return [Habitat.from_dict(d) for d in self.state["habitats"]]

    def set_habitats(self, lst: List[Habitat]):
        self.state["habitats"] = [h.to_dict() for h in lst]

    # ---------- per-tick updates ----------
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
        # eggs don’t get hungry
        if a.stage != "egg":
            a.hunger = max(0, min(self.settings.HUNGER_MAX, a.hunger - self.settings.HUNGER_DECAY_PER_TICK))
            a.happiness = max(0, min(self.settings.HAPPINESS_MAX, a.happiness - self.settings.HAPPINESS_DECAY_PER_TICK))

    def habitat_income_tick(self):
        total = 0.0
        for a in self.get_armadillos():
            if a.habitat_id and a.stage in ("adult", "retired"):
                rarity_weight = (1.0 + a.rarity * self.settings.RARITY_YIELD_MULTIPLIER)
                # mood multipliers
                hunger_mult = self.settings.HUNGER_INCOME_MIN_MULT + (1 - self.settings.HUNGER_INCOME_MIN_MULT) * (a.hunger / self.settings.HUNGER_MAX)
                happy_mult = 1.0 + self.settings.HAPPINESS_INCOME_BONUS_MAX * (a.happiness / self.settings.HAPPINESS_MAX)
                total += self.settings.HABITAT_BASE_YIELD_PER_TICK * rarity_weight * hunger_mult * happy_mult
        if total > 0:
            self.econ.add_coins(total)

    def tick(self, dt):
        self.state["tick"] += 1
        arms = self.get_armadillos()
        for a in arms:
            self.advance_age_and_stage(a)
            self.mood_decay_tick(a)
        self.set_armadillos(arms)

        self.habitat_income_tick()
        self._payout_counter += 1
        if self._payout_counter >= self.settings.ECON_PAYOUT_INTERVAL_TICKS:
            self._payout_counter = 0

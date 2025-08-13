# services/state.py
from __future__ import annotations

import random
import time
from typing import Callable, Dict, List, Optional, Set

from models.armadillo import Armadillo
from models.habitat import Habitat
from models.breeding import BreedingJob, hatch_result
from services.economy import Economy


Observer = Callable[[], None]


class GameState:
    _instance: Optional["GameState"] = None

    @staticmethod
    def instance() -> "GameState":
        if not GameState._instance:
            GameState._instance = GameState()
        return GameState._instance

    # ----------------------------------------------------------------------

    def __init__(self):
        # Core
        self.coins: int = 0
        self.inventory: Dict[str, int] = {"food": 0, "toy": 0}
        self.armadillos: List[Armadillo] = []
        self.habitats: List[Habitat] = []
        self.breeding_queue: List[BreedingJob] = []
        self.dex_colors: Set[str] = set()
        self.selected_id: Optional[str] = None
        self.meta: Dict[str, any] = {}

        self._observers: List[Observer] = []

    # ---- Observers --------------------------------------------------------

    def add_observer(self, cb: Observer) -> None:
        if cb not in self._observers:
            self._observers.append(cb)

    def _notify(self) -> None:
        for cb in list(self._observers):
            try:
                cb()
            except Exception:
                pass

    # ---- Query helpers ----------------------------------------------------

    def get_selected(self) -> Optional[Armadillo]:
        if not self.selected_id:
            return None
        for d in self.armadillos:
            if d.id == self.selected_id:
                return d
        return None

    def get_by_id(self, did: str) -> Optional[Armadillo]:
        for d in self.armadillos:
            if d.id == did:
                return d
        return None

    # ---- Mutations (all call _notify) ------------------------------------

    def seed_starters(self) -> None:
        self.coins = 100
        self.inventory = {"food": 3, "toy": 1}
        self.armadillos = [
            Armadillo(id="d1", name="Rocky", sex="M", age_days=20, hunger=70, happiness=65, genes={"color": "Aa"}, color="Brown", is_baby=False, is_adult=True),
            Armadillo(id="d2", name="Pearl", sex="F", age_days=22, hunger=55, happiness=70, genes={"color": "aa"}, color="Albino", is_baby=False, is_adult=True),
            Armadillo(id="d3", name="Indigo", sex="M", age_days=5, hunger=60, happiness=60, genes={"color": "AB"}, color="Blue", is_baby=True, is_adult=False),
        ]
        self.habitats = [
            Habitat(id="h1", name="Meadow", level=1, capacity=2, occupants=["d1"]),
            Habitat(id="h2", name="Cave", level=1, capacity=1, occupants=["d2"]),
            Habitat(id="h3", name="Coast", level=1, capacity=1, occupants=[]),
        ]
        self.dex_colors = {a.color for a in self.armadillos}
        self.selected_id = None
        self.breeding_queue = []
        self._notify()

    def select(self, did: Optional[str]) -> None:
        self.selected_id = did
        self._notify()

    def add_coins(self, amt: int) -> None:
        self.coins = max(0, self.coins + amt)
        self._notify()

    def buy(self, item: str, cost: int) -> bool:
        if self.coins >= cost:
            self.coins -= cost
            if item in self.inventory:
                self.inventory[item] += 1
            else:
                self.inventory[item] = 1
            self._notify()
            return True
        return False

    def upgrade_habitat(self, hid: str, cost: int, capacity_delta: int) -> bool:
        if self.coins < cost:
            return False
        for h in self.habitats:
            if h.id == hid:
                self.coins -= cost
                h.level += 1
                h.capacity += capacity_delta
                self._notify()
                return True
        return False

    def feed_selected(self) -> bool:
        d = self.get_selected()
        if not d or self.inventory.get("food", 0) <= 0:
            return False
        self.inventory["food"] -= 1
        d.feed(20)
        # Bonus coins if both stats high
        if d.hunger > 80 and d.happiness > 80:
            self.add_coins(Economy.REWARD_CARE)
        else:
            self._notify()
        return True

    def pet_selected(self) -> bool:
        d = self.get_selected()
        if not d:
            return False
        d.pet(15)
        if d.hunger > 80 and d.happiness > 80:
            self.add_coins(Economy.REWARD_CARE)
        else:
            self._notify()
        return True

    def move_selected_to_habitat(self, hid: str) -> bool:
        d = self.get_selected()
        if not d:
            return False
        # Remove from any current habitat
        for h in self.habitats:
            if d.id in h.occupants:
                h.remove(d.id)
        # Add to target if space
        for h in self.habitats:
            if h.id == hid:
                if h.add(d.id):
                    self._notify()
                    return True
                return False
        return False

    def adults(self) -> List[Armadillo]:
        return [a for a in self.armadillos if a.is_adult]

    def start_breeding(self, dad_id: str, mom_id: str, duration_s: int) -> Optional[BreedingJob]:
        if dad_id == mom_id:
            return None
        dad = self.get_by_id(dad_id)
        mom = self.get_by_id(mom_id)
        if not dad or not mom or dad.sex != "M" or mom.sex != "F" or not dad.is_adult or not mom.is_adult:
            return None
        job = BreedingJob(
            id=f"job_{int(time.time()*1000)}",
            parent_m_id=dad_id,
            parent_f_id=mom_id,
            start_ts=time.time(),
            duration_s=duration_s,
            status="incubating",
        )
        self.breeding_queue.append(job)
        self._notify()
        return job

    def breeding_tick(self, now: float):
        hatched = []
        for job in self.breeding_queue:
            if job.is_done(now):
                dad = self.get_by_id(job.parent_m_id)
                mom = self.get_by_id(job.parent_f_id)
                if not dad or not mom:
                    job.status = "done"
                    continue
                # Hatch
                baby_dict = hatch_result(dad, mom, job.duration_s, Economy.MUTATION_CHANCE)
                job.status = "done"
                job.result = baby_dict
                # Add baby
                baby = Armadillo.from_dict(baby_dict)
                # Baby grows into habitat of mom if space
                for h in self.habitats:
                    if mom.id in h.occupants and h.has_space():
                        h.add(baby.id)
                        break
                # Add to roster
                self.armadillos.append(baby)
                self.dex_colors.add(baby.color)
                hatched.append(baby)
        # Remove finished
        if hatched:
            self.breeding_queue = [j for j in self.breeding_queue if j.status != "done"]
            self._notify()
        return hatched

    # ---- Serialization -----------------------------------------------------

    def to_dict(self) -> dict:
        return {
            "coins": self.coins,
            "inventory": dict(self.inventory),
            "armadillos": [a.to_dict() for a in self.armadillos],
            "habitats": [h.to_dict() for h in self.habitats],
            "breeding_queue": [j.to_dict() for j in self.breeding_queue],
            "dex_colors": list(self.dex_colors),
            "selected_id": self.selected_id,
            "meta": dict(self.meta),
        }

    def from_dict(self, d: dict) -> None:
        self.coins = int(d.get("coins", 0))
        self.inventory = dict(d.get("inventory", {}))
        self.armadillos = [Armadillo.from_dict(x) for x in d.get("armadillos", [])]
        self.habitats = [Habitat.from_dict(x) for x in d.get("habitats", [])]
        self.breeding_queue = [BreedingJob.from_dict(x) for x in d.get("breeding_queue", [])]
        self.dex_colors = set(d.get("dex_colors", []))
        self.selected_id = d.get("selected_id")
        self.meta = dict(d.get("meta", {}))
        # Recompute adult flags (simple: >= 14 days -> adult)
        for a in self.armadillos:
            a.is_adult = a.age_days >= 14
            a.is_baby = not a.is_adult
        self._notify()

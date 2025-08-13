# models/armadillo.py
from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Dict


@dataclass
class Armadillo:
    id: str
    name: str
    sex: str  # "M" or "F"
    age_days: int
    hunger: int  # 0-100 (higher = fuller)
    happiness: int  # 0-100
    genes: Dict[str, str]  # simple genotype mapping e.g., {"color": "Aa"}
    color: str  # phenotype, e.g., "Brown", "Albino", "Blue"
    is_baby: bool
    is_adult: bool

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "Armadillo":
        return Armadillo(
            id=d["id"],
            name=d["name"],
            sex=d["sex"],
            age_days=int(d.get("age_days", 0)),
            hunger=int(d.get("hunger", 50)),
            happiness=int(d.get("happiness", 50)),
            genes=dict(d.get("genes", {})),
            color=d.get("color", "Brown"),
            is_baby=bool(d.get("is_baby", False)),
            is_adult=bool(d.get("is_adult", True)),
        )

    # --- Stats manipulation (capped) ---------------------------------------

    def feed(self, amount: int) -> None:
        self.hunger = max(0, min(100, self.hunger + amount))

    def pet(self, amount: int) -> None:
        self.happiness = max(0, min(100, self.happiness + amount))

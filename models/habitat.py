# models/habitat.py
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import List


@dataclass
class Habitat:
    id: str
    name: str
    level: int
    capacity: int
    occupants: List[str] = field(default_factory=list)  # armadillo ids
    hatch_boost_pct: int = 0  # small % boost

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "Habitat":
        return Habitat(
            id=d["id"],
            name=d["name"],
            level=int(d.get("level", 1)),
            capacity=int(d.get("capacity", 2)),
            occupants=list(d.get("occupants", [])),
            hatch_boost_pct=int(d.get("hatch_boost_pct", 0)),
        )

    def has_space(self) -> bool:
        return len(self.occupants) < self.capacity

    def add(self, armadillo_id: str) -> bool:
        if self.has_space() and armadillo_id not in self.occupants:
            self.occupants.append(armadillo_id)
            return True
        return False

    def remove(self, armadillo_id: str) -> None:
        if armadillo_id in self.occupants:
            self.occupants.remove(armadillo_id)

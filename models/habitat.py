from dataclasses import dataclass, asdict
from typing import Dict, List


@dataclass
class Habitat:
    id: str
    name: str
    biome: str  # "desert","forest","savannah"
    capacity: int

    def to_dict(self) -> Dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: Dict) -> "Habitat":
        return Habitat(**d)

    @staticmethod
    def new_default(settings) -> "Habitat":
        return Habitat(
            id="hab_001",
            name="Starter Pen",
            biome="desert",
            capacity=settings.DEFAULT_HABITAT_CAPACITY
        )

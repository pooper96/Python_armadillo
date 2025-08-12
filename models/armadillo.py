from typing import Dict, Tuple
from dataclasses import dataclass, asdict
from models.genetics import RNG, mix_color_with_variance, inherit_traits


@dataclass
class Armadillo:
    id: str
    nickname: str
    rgb: Tuple[float, float, float]
    hex_color: str
    weight: float  # 0.5..1.5 (demo-friendly)
    age_ticks: int
    stage: str  # "egg","juvenile","adult","retired"
    sex: str    # "M" or "F"
    traits: Dict[str, tuple]  # each: (allele_a, allele_b, phenotype)
    rarity: float  # 0..1 used for yield scaling
    habitat_id: str | None

    def to_dict(self) -> Dict:
        d = asdict(self)
        d["rgb"] = list(self.rgb)
        return d

    @staticmethod
    def from_dict(d: Dict) -> "Armadillo":
        d = dict(d)
        d["rgb"] = tuple(d["rgb"])
        return Armadillo(**d)

    @staticmethod
    def new_starter(settings, nickname="Armi") -> "Armadillo":
        # pleasant desert-ish starter tones
        r, g, b = 0.75, 0.65, 0.5
        sex = "M" if RNG.randint(0, 1) == 0 else "F"
        traits = {
            "pattern": ("banded", "plain", "banded"),
            "ears": ("tall", "short", "tall"),
        }
        return Armadillo(
            id=f"arm_{RNG.randint(100000,999999)}",
            nickname=nickname,
            rgb=(r, g, b),
            hex_color="#C0A580",
            weight=1.0,
            age_ticks=0,
            stage="juvenile",
            sex=sex,
            traits=traits,
            rarity=0.35,
            habitat_id=None
        )

    def is_adult(self, settings) -> bool:
        return self.stage == "adult"

    def can_breed(self, settings) -> bool:
        return self.is_adult(settings)

    @staticmethod
    def breed(settings, mom: "Armadillo", dad: "Armadillo") -> "Armadillo":
        child_rgb, child_hex = mix_color_with_variance(
            mom.rgb, dad.rgb,
            settings.VARIANCE_STD, settings.MAX_VARIANCE,
            settings.WEIGHT_VARIANCE_FACTOR, settings.AGE_VARIANCE_FACTOR,
            mom.weight, dad.weight,
            mom.age_ticks, dad.age_ticks
        )
        child_traits = inherit_traits(mom.traits, dad.traits, settings.BASE_MUTATION_CHANCE)
        rarity = max(0.1, min(1.0, (mom.rarity + dad.rarity) / 2.0))
        sex = "M" if RNG.randint(0, 1) == 0 else "F"
        return Armadillo(
            id=f"arm_{RNG.randint(100000,999999)}",
            nickname="Egg",
            rgb=child_rgb,
            hex_color=child_hex,
            weight=max(0.5, min(1.5, (mom.weight + dad.weight) / 2.0 + (RNG.random() - 0.5) * 0.1)),
            age_ticks=0,
            stage="egg",
            sex=sex,
            traits=child_traits,
            rarity=rarity,
            habitat_id=None
        )

# models/breeding.py
from __future__ import annotations

import random
import time
from dataclasses import dataclass, asdict
from typing import Optional, Dict, Tuple

from models.armadillo import Armadillo


@dataclass
class BreedingJob:
    id: str
    parent_m_id: str
    parent_f_id: str
    start_ts: float
    duration_s: int
    status: str  # "incubating" | "done"
    result: Optional[Dict] = None  # newborn dict if done

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "BreedingJob":
        return BreedingJob(
            id=d["id"],
            parent_m_id=d["parent_m_id"],
            parent_f_id=d["parent_f_id"],
            start_ts=float(d["start_ts"]),
            duration_s=int(d["duration_s"]),
            status=d.get("status", "incubating"),
            result=d.get("result"),
        )

    def remaining(self, now: Optional[float] = None) -> int:
        now = now or time.time()
        rem = int(self.start_ts + self.duration_s - now)
        return max(0, rem)

    def is_done(self, now: Optional[float] = None) -> bool:
        return self.remaining(now) <= 0 and self.status != "done"


# ---- Genetics --------------------------------------------------------------


def combine_genes(color_m: str, color_f: str, mutation_chance: float) -> Tuple[str, str]:
    """
    Very simple Mendelian-ish color system:
    - Alleles: A (dominant, Brown), a (recessive, Albino)
    - Secondary rare: B (Blue) emerges with small mutation chance.
    Parents pass one allele each randomly.
    """
    alleles_m = list(color_m)
    alleles_f = list(color_f)
    child = random.choice(alleles_m) + random.choice(alleles_f)

    # Mutation: small chance to become blue phenotype "B?"
    if random.random() < mutation_chance:
        # flip one allele to 'B' to denote blue trait carrier
        idx = random.randrange(2)
        child = ("B" if idx == 0 else child[0]) + ("B" if idx == 1 else child[1])

    # Phenotype
    if "B" in child:
        phenotype = "Blue"
    elif "A" in child:
        phenotype = "Brown"
    else:
        phenotype = "Albino"

    # Normalize genes to 2 chars
    if len(child) < 2:
        child = (child + "a")[:2]
    return child, phenotype


def make_baby_name() -> str:
    pool = ["Pico", "Mina", "Sable", "Roly", "Dot", "Tango", "Nori", "Churro", "Fika", "Biscuit"]
    return random.choice(pool)


def hatch_result(dad: Armadillo, mom: Armadillo, base_duration: int, mutation_chance: float) -> Dict:
    genes, color = combine_genes(dad.genes.get("color", "Aa"), mom.genes.get("color", "Aa"), mutation_chance)
    sex = random.choice(["M", "F"])
    baby = Armadillo(
        id=f"dillo_{int(time.time()*1000)}",
        name=make_baby_name(),
        sex=sex,
        age_days=0,
        hunger=60,
        happiness=60,
        genes={"color": genes},
        color=color,
        is_baby=True,
        is_adult=False,
    )
    return baby.to_dict()

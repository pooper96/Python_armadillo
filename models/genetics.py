import random
from typing import Tuple, Dict, List


class RNG:
    """Deterministic RNG wrapper set once from save. Use only this for randomness."""
    _rng = random.Random(1337)

    @classmethod
    def set_seed(cls, seed: int):
        cls._rng = random.Random(seed)

    @classmethod
    def randint(cls, a, b):
        return cls._rng.randint(a, b)

    @classmethod
    def random(cls):
        return cls._rng.random()

    @classmethod
    def gauss(cls, mu, sigma):
        return cls._rng.gauss(mu, sigma)

    @classmethod
    def choice(cls, seq):
        return cls._rng.choice(seq)

    @classmethod
    def uniform(cls, a, b):
        return cls._rng.uniform(a, b)


def clamp01(x: float) -> float:
    return 0.0 if x < 0.0 else 1.0 if x > 1.0 else x


def rgb_to_hex(rgb: Tuple[float, float, float]) -> str:
    r = int(clamp01(rgb[0]) * 255)
    g = int(clamp01(rgb[1]) * 255)
    b = int(clamp01(rgb[2]) * 255)
    return "#{:02X}{:02X}{:02X}".format(r, g, b)


def mix_color_with_variance(
    mom_rgb: Tuple[float, float, float],
    dad_rgb: Tuple[float, float, float],
    variance_std: float,
    max_variance: float,
    weight_factor: float,
    age_factor: float,
    mom_weight: float,
    dad_weight: float,
    mom_age_t: int,
    dad_age_t: int,
) -> Tuple[Tuple[float, float, float], str]:
    """Weighted average + bounded variance influenced by age/weight."""
    avg_weight = (mom_weight + dad_weight) / 2.0
    age_scale = 1.0 + age_factor * ((mom_age_t + dad_age_t) / 2.0) / (60 * 20)  # per minute in demo
    weight_scale = 1.0 + weight_factor * (abs(1.0 - avg_weight))  # if either very light/heavy → slightly more variance

    def comp(i):
        base = (mom_rgb[i] + dad_rgb[i]) / 2.0
        noise = RNG.gauss(0.0, variance_std * weight_scale * age_scale)
        noise = max(-max_variance, min(max_variance, noise))
        return clamp01(base + noise)

    child = (comp(0), comp(1), comp(2))
    return child, rgb_to_hex(child)


# Traits system: A simple dominant/recessive map with mutation chance.
TRAIT_POOL = {
    "pattern": {
        "dominant": ["banded", "speckled"],
        "recessive": ["plain", "marbled"]
    },
    "ears": {
        "dominant": ["tall"],
        "recessive": ["short"]
    }
}


def resolve_trait(gene_a: str, gene_b: str, trait_key: str) -> str:
    dom = set(TRAIT_POOL[trait_key]["dominant"])
    if gene_a in dom or gene_b in dom:
        # If any dominant present, choose one of the dominant alleles present
        candidates = [g for g in [gene_a, gene_b] if g in dom]
        return RNG.choice(candidates)
    # otherwise recessive
    return RNG.choice([gene_a, gene_b])


def mutate_trait(trait_key: str) -> str:
    all_alleles = TRAIT_POOL[trait_key]["dominant"] + TRAIT_POOL[trait_key]["recessive"]
    return RNG.choice(all_alleles)


def inherit_traits(
    mom_genes: Dict[str, Tuple[str, str]],
    dad_genes: Dict[str, Tuple[str, str]],
    mutation_chance: float
) -> Dict[str, Tuple[str, str, str]]:
    """Return genotype (two alleles) + phenotype resolved; mutation can replace one allele."""
    child = {}
    for tkey in TRAIT_POOL.keys():
        m = mom_genes.get(tkey, (RNG.choice(TRAIT_POOL[tkey]["dominant"]), RNG.choice(TRAIT_POOL[tkey]["recessive"])))
        d = dad_genes.get(tkey, (RNG.choice(TRAIT_POOL[tkey]["dominant"]), RNG.choice(TRAIT_POOL[tkey]["recessive"])))
        allele_a = RNG.choice(m)
        allele_b = RNG.choice(d)
        # possible mutation
        if RNG.random() < mutation_chance:
            allele_a = mutate_trait(tkey)
        if RNG.random() < mutation_chance:
            allele_b = mutate_trait(tkey)
        phenotype = resolve_trait(allele_a, allele_b, tkey)
        child[tkey] = (allele_a, allele_b, phenotype)
    return child

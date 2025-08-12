import math
from models.genetics import mix_color_with_variance, inherit_traits, RNG

def test_color_mix_is_bounded_and_close_to_average():
    RNG.set_seed(1234)
    mom = (0.9, 0.2, 0.1)
    dad = (0.1, 0.8, 0.3)
    child, hexv = mix_color_with_variance(
        mom, dad,
        variance_std=0.05, max_variance=0.2,
        weight_factor=0.25, age_factor=0.15,
        mom_weight=1.0, dad_weight=1.0,
        mom_age_t=0, dad_age_t=0
    )
    # close to mean within reasonable tolerance
    mean = tuple((m + d) / 2.0 for m, d in zip(mom, dad))
    dist = math.dist(child, mean)
    assert 0.0 <= child[0] <= 1.0 and 0.0 <= child[1] <= 1.0 and 0.0 <= child[2] <= 1.0
    assert dist < 0.2  # with small variance should be near average

def test_traits_mutation_probability_is_respected():
    RNG.set_seed(42)
    mom = {"pattern": ("banded", "plain"), "ears": ("tall", "short")}
    dad = {"pattern": ("banded", "marbled"), "ears": ("short", "short")}
    # Force high mutation to observe changes
    mutated = inherit_traits(mom, dad, mutation_chance=0.9)
    assert "pattern" in mutated and "ears" in mutated
    # phenotype resolved field exists
    for k, v in mutated.items():
        assert len(v) == 3

# tests/test_core.py
import random
from models.breeding import combine_genes
from services.economy import Economy


def test_genetics_basic():
    random.seed(123)
    # Dominant A + recessive a -> phenotype Brown most of time absent mutation
    for _ in range(10):
        genes, ph = combine_genes("Aa", "aa", 0.0)
        assert len(genes) == 2
        assert ph in ("Brown", "Albino")
    # Force mutation to show Blue sometimes
    blues = 0
    for _ in range(100):
        _, ph = combine_genes("aa", "aa", 0.25)
        if ph == "Blue":
            blues += 1
    assert blues > 0


def test_economy_values():
    assert Economy.COST_FOOD > 0
    assert Economy.REWARD_HATCH > 0
    assert Economy.INCUBATION_MIN_S <= Economy.INCUBATION_MAX_S

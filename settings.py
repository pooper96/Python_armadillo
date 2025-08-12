from dataclasses import dataclass


@dataclass(frozen=True)
class Settings:
    # Simulation / timing
    TICKS_PER_SEC: int = 20
    AUTOSAVE_INTERVAL_SEC: int = 30
    ECON_PAYOUT_INTERVAL_TICKS: int = 60  # once every 3 seconds at 20 tps

    # RNG / Genetics
    BASE_MUTATION_CHANCE: float = 0.02
    VARIANCE_STD: float = 0.06  # base RGB variance
    MAX_VARIANCE: float = 0.18
    WEIGHT_VARIANCE_FACTOR: float = 0.25
    AGE_VARIANCE_FACTOR: float = 0.15

    # Armadillo stages (in ticks)
    EGG_TICKS: int = 20 * 20        # 20s to hatch
    JUVENILE_TICKS: int = 120 * 20  # 2 min to adult in demo
    ADULT_TICKS: int = 99999999     # stays adult until retirement condition hit
    RETIRE_AGE_TICKS: int = 10 * 60 * 20  # 10 minutes demo retire

    # Habitat
    DEFAULT_HABITAT_CAPACITY: int = 6
    HABITAT_BASE_YIELD_PER_TICK: float = 0.02  # base coins per tick per rarity weight
    RARITY_YIELD_MULTIPLIER: float = 2.0

    # Economy
    STARTING_COINS: int = 200
    FEED_COST: int = 2
    INCUBATOR_BASE_COST: int = 50

    # UI / drawing
    SCREEN_W: int = 900
    SCREEN_H: int = 520
    BG_LAYERS: int = 3
    SHADOW_ALPHA: float = 0.25

    # Save
    SAVE_FILENAME: str = "armadillo_farmer_save.json"
    SAVE_SCHEMA_VERSION: int = 1

    # Accessibility
    ENABLE_COLORBLIND_NUMERIC_TAGS: bool = True

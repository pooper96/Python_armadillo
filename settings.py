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
    EGG_TICKS: int = 20 * 20
    JUVENILE_TICKS: int = 120 * 20
    ADULT_TICKS: int = 99999999
    RETIRE_AGE_TICKS: int = 10 * 60 * 20

    # Habitat
    DEFAULT_HABITAT_CAPACITY: int = 6
    HABITAT_BASE_YIELD_PER_TICK: float = 0.02
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

    # --- Animation / Home scene ---
    ARM_SPEED_MIN: float = 40.0     # px/s
    ARM_SPEED_MAX: float = 95.0     # px/s
    ARM_MARGIN_X: float = 32.0      # left/right padding inside the pen
    PIXEL_SCALE_MIN: float = 4.0
    PIXEL_SCALE_MAX: float = 10.0

    # --- Care stats ---
    HUNGER_MAX: int = 100
    HAPPINESS_MAX: int = 100
    HUNGER_DECAY_PER_TICK: float = 0.05    # ~1 per sec at 20 tps
    HAPPINESS_DECAY_PER_TICK: float = 0.02 # ~0.4 per sec
    FEED_HUNGER_GAIN: int = 20
    PET_HAPPINESS_GAIN: int = 15

    # Income scaling by mood (applied in habitat payouts)
    HUNGER_INCOME_MIN_MULT: float = 0.3    # starving earns 30%
    HAPPINESS_INCOME_BONUS_MAX: float = 0.2  # +20% at 100 happiness

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
    ARM_SPEED_MIN: float = 35.0     # px/s
    ARM_SPEED_MAX: float = 80.0     # px/s
    ARM_BOB_AMPLITUDE: float = 6.0  # px vertical bob
    ARM_BOB_FREQ: float = 1.2       # cycles per second
    ARM_MARGIN_X: float = 24.0      # left/right padding inside the pen

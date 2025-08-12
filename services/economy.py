from typing import Dict
from settings import Settings


class EconomyService:
    def __init__(self, settings: Settings, state: Dict):
        self.settings = settings
        self.state = state

    def add_coins(self, amount: int | float):
        self.state["coins"] = int(max(0, self.state.get("coins", 0) + amount))

    def spend(self, amount: int) -> bool:
        if self.state.get("coins", 0) >= amount:
            self.state["coins"] -= amount
            return True
        return False

    def feed_cost(self) -> int:
        return self.settings.FEED_COST

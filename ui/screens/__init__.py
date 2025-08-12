# Marks 'ui.screens' as a package and re-exports screens (optional).
from .home import HomeScreen
from .habitats import HabitatsScreen
from .breeding import BreedingScreen
from .dex import DexScreen
from .shop import ShopScreen

__all__ = [
    "HomeScreen", "HabitatsScreen", "BreedingScreen", "DexScreen", "ShopScreen"
]

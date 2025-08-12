class UIState:
    """Ephemeral UI state shared between screens (not saved)."""
    def __init__(self):
        self.selected_armadillo_id: str | None = None

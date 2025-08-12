class UIState:
    """Ephemeral UI state shared between screens (not saved)."""
    def __init__(self):
        self.selected_armadillo_id: str | None = None

        # Drag state for Home screen
        self.dragging_id: str | None = None
        self._drag_touch_uid: int | None = None
        self._drag_started: bool = False
        self.drag_pos = (0, 0)

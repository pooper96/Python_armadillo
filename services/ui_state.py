class UIState:
    """Ephemeral UI state shared between screens (not saved)."""
    def __init__(self):
        # selection
        self.selected_armadillo_id: str | None = None

        # drag state (Home screen)
        self.dragging_id: str | None = None
        self._drag_touch_uid: int | None = None
        self._drag_started: bool = False
        self.drag_pos = (0, 0)

        # press-to-drag detection
        self._down_arm_id: str | None = None
        self._down_pos = (0.0, 0.0)
        self.DRAG_THRESHOLD_PX: float = 10.0

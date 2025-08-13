# services/persistence.py
from __future__ import annotations

import json
import os
from typing import Optional

from kivy.app import App

from services.state import GameState


class Persistence:
    def __init__(self):
        self._path = None

    def _save_path(self) -> str:
        if self._path:
            return self._path
        app = App.get_running_app()
        base = app.user_data_dir if app else os.path.join(os.getcwd(), ".userdata")
        if not os.path.isdir(base):
            os.makedirs(base, exist_ok=True)
        self._path = os.path.join(base, "save.json")
        return self._path

    def save(self, state: GameState) -> bool:
        path = self._save_path()
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(state.to_dict(), f, indent=2)
            return True
        except Exception:
            return False

    def load(self, state: GameState) -> bool:
        path = self._save_path()
        if not os.path.exists(path):
            return False
        try:
            with open(path, "r", encoding="utf-8") as f:
                d = json.load(f)
            state.from_dict(d)
            return True
        except Exception:
            return False

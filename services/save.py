import os, tempfile, json, ujson
from typing import Dict
from pathlib import Path
from kivy.app import App

from settings import Settings
from models.genetics import RNG


class SaveService:
    def __init__(self, settings: Settings):
        self.settings = settings
        # Use platform-safe per-app directory (Android/iOS/desktop)
        user_dir = Path(App.get_running_app().user_data_dir)
        user_dir.mkdir(parents=True, exist_ok=True)
        self._path = str(user_dir / self.settings.SAVE_FILENAME)
        self._last_hash = None  # for change-aware autosave

    def _state_hash(self, state: Dict) -> str:
        """Stable content hash so we only write when something changed."""
        import hashlib
        # json (not ujson) for sort_keys to produce deterministic blob
        blob = json.dumps(state, sort_keys=True, separators=(",", ":")).encode("utf-8")
        return hashlib.sha256(blob).hexdigest()

    def default_state(self) -> Dict:
        return {
            "schema_version": self.settings.SAVE_SCHEMA_VERSION,
            "rng_seed": RNG.randint(1000, 10_000_000),
            "coins": self.settings.STARTING_COINS,
            "habitats": [],
            "armadillos": [],
            "incubator": [],  # queue of egg ids
            "collections": {},
            "tick": 0,
        }

    def migrate(self, state: Dict) -> Dict:
        # reserved for future schema bumps
        return state

    def load_or_init(self) -> Dict:
        if not os.path.exists(self._path):
            state = self.default_state()
            self.atomic_save(state)  # initial write
            self._last_hash = self._state_hash(state)
            return state

        with open(self._path, "r", encoding="utf-8") as f:
            text = f.read()
            try:
                state = ujson.loads(text)
            except Exception:
                state = json.loads(text)
        state = self.migrate(state)
        self._last_hash = self._state_hash(state)
        return state

    def atomic_save(self, state: Dict):
        tmp_fd, tmp_path = tempfile.mkstemp(prefix="armadillo_save_", suffix=".tmp")
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as tmpf:
                tmpf.write(ujson.dumps(state, ensure_ascii=False))
                tmpf.flush()
                os.fsync(tmpf.fileno())
            os.replace(tmp_path, self._path)
            self._last_hash = self._state_hash(state)
        finally:
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass

    def atomic_save_if_dirty(self, state: Dict):
        """Only write if content actually changed since last save."""
        h = self._state_hash(state)
        if h != self._last_hash:
            self.atomic_save(state)

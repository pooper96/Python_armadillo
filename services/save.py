import os, tempfile, json, ujson
from typing import Dict
from settings import Settings
from models.genetics import RNG


class SaveService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self._path = self.settings.SAVE_FILENAME

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
            self.atomic_save(state)
            return state
        with open(self._path, "r", encoding="utf-8") as f:
            text = f.read()
            try:
                # try ujson first for speed
                state = ujson.loads(text)
            except Exception:
                state = json.loads(text)
        return self.migrate(state)

    def atomic_save(self, state: Dict):
        tmp_fd, tmp_path = tempfile.mkstemp(prefix="armadillo_save_", suffix=".tmp")
        try:
            with os.fdopen(tmp_fd, "w", encoding="utf-8") as tmpf:
                tmpf.write(ujson.dumps(state, ensure_ascii=False))
                tmpf.flush()
                os.fsync(tmpf.fileno())
            os.replace(tmp_path, self._path)
        finally:
            try:
                if os.path.exists(tmp_path):
                    os.remove(tmp_path)
            except Exception:
                pass

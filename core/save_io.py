# core/save_io.py
from __future__ import annotations
import json
from pathlib import Path
from typing import Any, Dict
from kivy.app import App

SAVE_NAME = "armadillo_farmer_save.json"

def save_dir() -> Path:
    app = App.get_running_app()
    p = Path(app.user_data_dir)
    p.mkdir(parents=True, exist_ok=True)
    return p

def save_path() -> Path:
    return save_dir() / SAVE_NAME

def load_state() -> Dict[str, Any]:
    p = save_path()
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:
        return {}

def save_state_atomic(state: Dict[str, Any]) -> None:
    p = save_path()
    tmp = p.with_suffix(".tmp")
    tmp.write_text(json.dumps(state, ensure_ascii=False), encoding="utf-8")
    tmp.replace(p)

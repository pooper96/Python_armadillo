# tests/test_save_roundtrip.py
from services.save import SaveService
from settings import Settings

def test_save_load_roundtrip(tmp_path, monkeypatch):
    s = Settings()
    ss = SaveService(s)
    # redirect path to tmp
    from kivy.app import App
    class DummyApp: user_data_dir = str(tmp_path)
    monkeypatch.setattr(App, "get_running_app", lambda: DummyApp())

    state = ss.default_state()
    ss.atomic_save(state)
    loaded = ss.load_or_init()
    assert loaded["schema_version"] == state["schema_version"]
    assert loaded["rng_seed"] == state["rng_seed"]
    assert loaded["coins"] == state["coins"]

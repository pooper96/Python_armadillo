# tests/smoke_test.py
# Minimal sanity checks: widgets instantiate, screens load.
import pytest

def test_imports():
    import kivy  # noqa
    from ui import constants, widgets, drag  # noqa
    from ui.formerscreen import home, habitats, breeding, dex, shop  # noqa

def test_app_builds(monkeypatch):
    from main import ArmadilloApp
    app = ArmadilloApp()
    root = app.build()
    assert root is not None
    # Switch through tabs
    for tab in ["home", "habitats", "breeding", "dex", "shop"]:
        root.switch_to(tab)
        assert root.sm.current == tab

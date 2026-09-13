from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")


def ambient_toggle_handler():
    menu = APP[APP.index("function showGameMenu()") : APP.index("function showAbout()")]
    return menu[
        menu.index("$('#ambientNoiseToggle').onclick") :
        menu.index("$('#diceRollToggle').onclick")
    ]


def test_v1005_release_metadata_is_consistent():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) >= (10, 0, 5)
    index = (ROOT / "index.html").read_text(encoding="utf-8")
    worker = (ROOT / "service-worker.js").read_text(encoding="utf-8")
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    assert f"V{CURRENT_APP_VERSION}" in index
    assert "10.0.4" not in index
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in worker
    assert readme.startswith(
        f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}\n\n## v{CURRENT_APP_VERSION}"
    )


def test_ambient_toggle_persists_then_immediately_applies_runtime_state():
    handler = ambient_toggle_handler()
    operations = [
        "ambientEnabled=!ambientEnabled",
        "localStorage.setItem(AMBIENT_ENABLED_PREFERENCE_KEY,String(ambientEnabled))",
        "appliedAmbientEnabled=ambientEnabled",
        "if(ambientEnabled){",
        "reconcileAmbientActiveState()",
        "if(shouldAmbientBeActive())void TombWorldAmbient.playFromGesture()",
        "}else TombWorldAmbient.stop()",
        "syncNarrationControls()",
    ]
    positions = [handler.index(operation) for operation in operations]
    assert positions == sorted(positions)


def test_ambient_toggle_does_not_change_other_audio_categories_or_reset_track():
    handler = ambient_toggle_handler()
    for unrelated_operation in (
        "TombWorldNarration.setMasterEnabled",
        "TombWorldNarration.setPreferenceEnabled",
        "TombWorldDiceSfx.setMasterEnabled",
        "TombWorldDiceSfx.setPreferenceEnabled",
        "TombWorldAmbient.reset",
        "currentTime",
    ):
        assert unrelated_operation not in handler

import json
import re
from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
STYLES = (ROOT / "styles.css").read_text(encoding="utf-8")


def test_v1002_release_surfaces_and_saved_game_contract():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) == (10, 0, 2)
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert f"analytics.js?release={CURRENT_APP_VERSION}" in INDEX
    assert INDEX.count(f"?v={CURRENT_APP_VERSION}") == 11
    assert "?v=9.2.63" not in INDEX
    assert "const CACHE_NAME = `${CACHE_PREFIX}${APP_VERSION}`;" in WORKER
    assert "const SAVE_VERSION = 3;" in (ROOT / "persistence.js").read_text(encoding="utf-8")
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    assert README.startswith(
        f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}\n\n"
        f"## v{CURRENT_APP_VERSION} - Setup Heading Focus Polish"
    )


def test_setup_heading_focus_decoration_is_scoped_without_removing_focus_management():
    assert ".wizard-shell .progress-head h2:focus,.wizard-shell .progress-head h2:focus-visible{outline:none;box-shadow:none}" in STYLES
    assert "setupHeading.tabIndex=-1;setupHeading.focus({preventScroll:true});" in APP
    assert "*:focus{outline:none}" not in STYLES.replace(" ", "")
    assert ".btn:focus-visible" in STYLES


def test_transcript_shell_and_manifest_derived_offline_media_contract():
    assert f'<script src="narration-transcript.js?v={CURRENT_APP_VERSION}"></script>' in INDEX
    assert "`./narration-transcript.js?v=${APP_VERSION}`" in WORKER
    assert "Object.entries(manifest.entries||{})" in WORKER
    assert "id.replace(/[^A-Za-z0-9._-]/g,'_')" in WORKER
    assert "...narration,...alignments" in WORKER

    manifest = json.loads((ROOT / "Assets/Audio/Narration/narration-manifest.json").read_text(encoding="utf-8"))
    available = [(entry_id, entry) for entry_id, entry in manifest["entries"].items() if entry.get("available") is True]
    expected_audio = {f"./Assets/Audio/Narration/{entry['file']}" for _, entry in available}
    expected_alignments = {
        "./Assets/Audio/Narration/alignment/" + re.sub(r"[^A-Za-z0-9._-]", "_", entry_id) + ".json"
        for entry_id, _ in available
    }
    assert len(available) == len(expected_audio) == len(expected_alignments) == 51
    assert all((ROOT / path.removeprefix("./")).is_file() for path in expected_audio | expected_alignments)


def test_production_runtime_has_no_elevenlabs_dependency_or_api_key():
    runtime_files = [
        ROOT / "index.html", ROOT / "app.js", ROOT / "narration.js",
        ROOT / "narration-transcript.js", ROOT / "service-worker.js",
    ]
    runtime = "\n".join(path.read_text(encoding="utf-8") for path in runtime_files).lower()
    assert "api.elevenlabs.io" not in runtime
    assert "xi-api-key" not in runtime

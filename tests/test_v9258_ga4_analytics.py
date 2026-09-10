import json
import subprocess
from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
ANALYTICS = (ROOT / "analytics.js").read_text(encoding="utf-8")
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")


def run_analytics(
    hostname, pathname, protocol="https:", online=True, runs=1, fail_append=False
):
    harness = f"""
const vm = require('node:vm');
const source = {json.dumps(ANALYTICS)};
const appended = [];
const context = {{
  window: {{location: {json.dumps({'hostname': hostname, 'pathname': pathname, 'protocol': protocol})}}},
  navigator: {{onLine: {json.dumps(online)}}},
  document: {{
    createElement: () => ({{}}),
    head: {{appendChild: element => {{
      if ({json.dumps(fail_append)}) throw new Error('head unavailable');
      appended.push(element);
    }}}}
  }},
  Date
}};
vm.createContext(context);
for (let run = 0; run < {runs}; run += 1) vm.runInContext(source, context);
const calls = (context.window.dataLayer || []).map(args => Array.from(args));
const tag = appended[0] || null;
if (tag && typeof tag.onerror === 'function') tag.onerror(new Error('blocked'));
process.stdout.write(JSON.stringify({{
  appended: appended.length,
  async: tag?.async,
  src: tag?.src,
  calls,
  initialized: Boolean(context.window.__tombWorldGa4Initialized)
}}));
"""
    result = subprocess.run(
        ["node", "-e", harness], check=True, capture_output=True, text=True
    )
    return json.loads(result.stdout)


def test_production_initializes_standard_ga4_once_without_duplicate_page_view():
    result = run_analytics(
        "imthekeymaster.github.io", "/TombWorldSoloGuide/", runs=2
    )
    assert result["appended"] == 1
    assert result["async"] is True
    assert result["src"] == (
        "https://www.googletagmanager.com/gtag/js?id=G-JWESVY3VFE"
    )
    assert [call[0] for call in result["calls"]] == ["js", "config"]
    assert result["calls"][1][1] == "G-JWESVY3VFE"
    assert result["calls"][1][2] == {
        "allow_google_signals": False,
        "allow_ad_personalization_signals": False,
    }
    assert "page_view" not in ANALYTICS


def test_nonproduction_and_offline_locations_do_not_initialize_ga4():
    rejected = [
        ("localhost", "/TombWorldSoloGuide/", "http:", True),
        ("127.0.0.1", "/TombWorldSoloGuide/", "http:", True),
        ("", "/workspace/index.html", "file:", True),
        ("fork.github.io", "/TombWorldSoloGuide/", "https:", True),
        ("imthekeymaster.github.io", "/AnotherGuide/", "https:", True),
        ("imthekeymaster.github.io", "/TombWorldSoloGuide/", "https:", False),
    ]
    for location in rejected:
        result = run_analytics(*location)
        assert result["appended"] == 0
        assert result["calls"] == []
        assert result["initialized"] is False


def test_analytics_module_is_isolated_nonblocking_and_contains_no_gameplay_data():
    assert (
        f'<script async src="analytics.js?release={CURRENT_APP_VERSION}"></script>'
        in INDEX
    )
    assert "gtag" not in APP.lower()
    assert APP.count("Usage Analytics:") == 1
    for forbidden in (
        "mission_started",
        "battle_started",
        "operative_activated",
        "dice_roll",
        "mission_complete",
        "victory",
        "defeat",
        "localStorage",
        "Background Sync",
    ):
        assert forbidden not in ANALYTICS
    assert "render(" not in ANALYTICS
    assert "googleTag.onerror = () => {};" in ANALYTICS


def test_analytics_initialization_failure_is_nonfatal():
    result = run_analytics(
        "imthekeymaster.github.io",
        "/TombWorldSoloGuide/",
        fail_append=True,
    )
    assert result["appended"] == 0


def test_analytics_assets_and_requests_preserve_offline_cache_boundaries():
    assert "`./analytics.js?release=${APP_VERSION}`" in WORKER
    for google_host in (
        "googletagmanager.com",
        "google-analytics.com",
        "analytics.google.com",
    ):
        assert google_host not in WORKER
    assert "if (url.origin !== self.location.origin) return;" in WORKER
    assert "queue" not in ANALYTICS.lower()


def test_disclosures_persistence_and_release_versions_are_consistent():
    disclosure = (
        "Usage Analytics:</strong> This Guide uses Google Analytics to understand "
        "aggregate site traffic such as visits, device type, and referral source."
    )
    assert disclosure in APP
    assert "**Usage Analytics:** This Guide uses Google Analytics" in README
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    assert "const SAVE_VERSION = 3;" in PERSISTENCE
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert INDEX.count(f"?v={CURRENT_APP_VERSION}") == 10
    assert README.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}\n\n## v{CURRENT_APP_VERSION}")
    assert "G-XXXXXXXXXX" not in "\n".join(
        path.read_text(encoding="utf-8")
        for path in (ROOT / "analytics.js", ROOT / "index.html", ROOT / "app.js")
    )

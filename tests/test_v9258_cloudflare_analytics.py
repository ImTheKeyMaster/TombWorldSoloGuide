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
PRODUCTION_SOURCE = "\n".join((ANALYTICS, APP, INDEX, WORKER, README))


def run_analytics(
    hostname,
    pathname,
    protocol="https:",
    online=True,
    runs=1,
    fail_lookup=False,
    fail_append=False,
):
    harness = f"""
const vm = require('node:vm');
const source = {json.dumps(ANALYTICS)};
const appended = [];
const document = {{
  getElementById: id => {{
    if ({json.dumps(fail_lookup)}) throw new Error('document unavailable');
    return appended.find(element => element.id === id) || null;
  }},
  createElement: () => ({{
    attributes: {{}},
    setAttribute(name, value) {{ this.attributes[name] = value; }}
  }}),
  head: {{appendChild: element => {{
    if ({json.dumps(fail_append)}) throw new Error('head unavailable');
    appended.push(element);
  }}}}
}};
const context = {{
  window: {{location: {json.dumps({'hostname': hostname, 'pathname': pathname, 'protocol': protocol})}}},
  navigator: {{onLine: {json.dumps(online)}}},
  document,
  JSON
}};
vm.createContext(context);
for (let run = 0; run < {runs}; run += 1) vm.runInContext(source, context);
const beacon = appended[0] || null;
if (beacon && typeof beacon.onerror === 'function') beacon.onerror(new Error('blocked'));
process.stdout.write(JSON.stringify({{
  appended: appended.length,
  id: beacon?.id,
  type: beacon?.type,
  src: beacon?.src,
  config: beacon?.attributes['data-cf-beacon']
}}));
"""
    result = subprocess.run(
        ["node", "-e", harness], check=True, capture_output=True, text=True
    )
    return json.loads(result.stdout)


def test_production_injects_one_cloudflare_module_beacon():
    result = run_analytics(
        "imthekeymaster.github.io", "/TombWorldSoloGuide/", runs=2
    )
    assert result["appended"] == 1
    assert result["id"] == "tomb-world-cloudflare-analytics"
    assert result["type"] == "module"
    assert result["src"] == "https://static.cloudflareinsights.com/beacon.min.js"
    assert json.loads(result["config"]) == {
        "token": "a5fcae7597364071bb35e87f0789706b"
    }


def test_nonproduction_and_offline_locations_do_not_inject_beacon():
    rejected = [
        ("localhost", "/TombWorldSoloGuide/", "http:", True),
        ("127.0.0.1", "/TombWorldSoloGuide/", "http:", True),
        ("::1", "/TombWorldSoloGuide/", "http:", True),
        ("", "/workspace/index.html", "file:", True),
        ("fork.github.io", "/TombWorldSoloGuide/", "https:", True),
        ("imthekeymaster.github.io", "/AnotherGuide/", "https:", True),
        ("imthekeymaster.github.io", "/TombWorldSoloGuide/", "http:", True),
        ("imthekeymaster.github.io", "/TombWorldSoloGuide/", "https:", False),
    ]
    for location in rejected:
        assert run_analytics(*location)["appended"] == 0


def test_analytics_failure_is_nonfatal_and_application_does_not_wait_for_it():
    for failure in ({"fail_lookup": True}, {"fail_append": True}):
        result = run_analytics(
            "imthekeymaster.github.io",
            "/TombWorldSoloGuide/",
            **failure,
        )
        assert result["appended"] == 0
    assert (
        f'<script async src="analytics.js?release={CURRENT_APP_VERSION}"></script>'
        in INDEX
    )
    assert "analytics.js" not in APP


def test_no_gameplay_custom_event_or_offline_queue_was_added():
    for forbidden in (
        "mission_started",
        "battle_started",
        "operative_activated",
        "dice_roll",
        "mission_complete",
        "localStorage",
        "indexedDB",
        "Background Sync",
    ):
        assert forbidden not in ANALYTICS
    assert "render(" not in ANALYTICS
    assert "addEventListener('online'" not in ANALYTICS


def test_external_cloudflare_resources_are_not_cached():
    assert "`./analytics.js?release=${APP_VERSION}`" in WORKER
    assert "static.cloudflareinsights.com" not in WORKER
    assert "beacon.min.js" not in WORKER
    assert "if (url.origin !== self.location.origin) return;" in WORKER


def test_google_analytics_and_consent_implementation_are_removed():
    for obsolete in (
        "G-JWESVY3VFE",
        "googletagmanager.com",
        "google-analytics.com",
        "analytics.google.com",
        "window.gtag",
        "window.dataLayer",
        "allow_google_signals",
        "allow_ad_personalization_signals",
        "analytics_storage",
        "Google Analytics",
        "GA4",
    ):
        assert obsolete not in PRODUCTION_SOURCE
    for consent_ui in (
        "Accept Analytics",
        "Reject Analytics",
        "consent modal",
        "analytics toggle",
    ):
        assert consent_ui not in PRODUCTION_SOURCE


def test_disclosures_persistence_and_release_versions_are_consistent():
    disclosure = (
        "Usage Analytics:</strong> This Guide uses Cloudflare Web Analytics to "
        "understand aggregate site traffic such as visits, device type, and referral source."
    )
    assert disclosure in APP
    assert "**Usage Analytics:** This Guide uses Cloudflare Web Analytics" in README
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP
    assert "const SAVE_VERSION = 3;" in PERSISTENCE
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert INDEX.count(f"?v={CURRENT_APP_VERSION}") == 11
    assert README.startswith(
        f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}\n\n## v{CURRENT_APP_VERSION}"
    )

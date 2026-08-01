import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
STYLES = (ROOT / "styles.css").read_text()
INDEX = (ROOT / "index.html").read_text()
WORKER = (ROOT / "service-worker.js").read_text()
README = (ROOT / "README.md").read_text()


def function_body(name):
    match = re.search(rf"  (?:async )?function {name}\([^\n]*", APP)
    if not match:
        return ""
    ends = [position for position in (
        APP.find("\n  function ", match.end()),
        APP.find("\n  async function ", match.end()),
    ) if position >= 0]
    return APP[match.start():min(ends) if ends else len(APP)]


def renderer(name, next_name=None):
    start = APP.index(f"    {name}:", APP.index("const missionProgressRenderers"))
    end = APP.index(f"    {next_name}:", start) if next_name else APP.index("\n  };", start)
    return APP[start:end]


class BattleCompleteCleanupTests(unittest.TestCase):
    def test_01_heading_retains_accessible_programmatic_focus(self):
        render = function_body("renderGame")
        self.assertIn('id="battle-complete-heading" tabindex="-1"', render)
        self.assertIn("requestAnimationFrame(()=>$('#battle-complete-heading')?.focus())", render)

    def test_02_focus_treatment_is_scoped_and_green(self):
        match = re.search(r"\.mission-outcome #battle-complete-heading:focus\s*\{([^}]+)\}", STYLES)
        self.assertIsNotNone(match)
        rule = match.group(1)
        self.assertIn("outline:3px solid var(--green)", rule)
        self.assertNotRegex(rule, r"blue|#(?:00f|007aff|0a84ff)\b")

    def test_03_read_only_mode_is_passed_explicitly(self):
        body = function_body("missionProgressHtml")
        self.assertIn("renderer(engine,progress,{readOnly})", body)
        self.assertIn("mission-objective-readonly", body)
        self.assertNotIn("inert", body)

    def test_04_completed_escape_keeps_names_statuses_and_count(self):
        body = renderer("escape", "sabotage")
        for text in ("playerName(id)", "operatives escaped", "Incapacitated", "Still in the killzone", "Escaped · Off Board"):
            self.assertIn(text, body)
        self.assertIn("readOnly||incapacitated||unavailable?'':", body)

    def test_05_completed_escape_omits_controls_instead_of_disabling_them(self):
        body = renderer("escape", "sabotage")
        control = body[body.index("readOnly||incapacitated||unavailable?'':"):]
        self.assertIn("Confirm Escape", control)
        self.assertIn("Undo Escape", control)
        self.assertNotIn("disabled", control)
        self.assertNotIn("aria-disabled", control)
        self.assertNotIn("hidden", control)

    def test_06_active_escape_controls_remain(self):
        body = renderer("escape", "sabotage")
        self.assertIn("data-mission-escaped", body)
        self.assertIn("escapedHere?'Undo Escape':'Confirm Escape'", body)

    def test_07_other_renderers_conditionally_omit_mutation_controls(self):
        sabotage = renderer("sabotage", "transponder")
        transponder = renderer("transponder", "destruction")
        destruction = renderer("destruction", "scout")
        scout = renderer("scout", "regroup")
        regroup = renderer("regroup")
        self.assertIn("readOnly?`<div", sabotage)
        self.assertIn("const assignment=readOnly?'':", transponder)
        self.assertIn("const escapeControl=readOnly?'':", transponder)
        self.assertIn("readOnly?finalState:", destruction)
        self.assertNotIn('id="resolveMissionAction"', destruction)
        self.assertIn("const actions=readOnly?'':", scout)
        self.assertIn("readOnly?`<span>", regroup)

    def test_08_other_active_renderers_retain_controls(self):
        all_renderers = APP[APP.index("const missionProgressRenderers"):APP.index("function missionProgressHtml")]
        for control in (
            'data-mission-feature', 'data-search-site', 'id="transponderCarrier"',
'data-awaken-room', 'data-scout-room',
            'data-regroup-check',
        ):
            self.assertIn(control, all_renderers)

    def test_09_read_only_rendering_does_not_mutate_progress(self):
        body = function_body("missionProgressHtml")
        self.assertNotRegex(body, r"progress\.[A-Za-z]+\s*=")
        self.assertNotIn("save()", body)
        self.assertNotIn("updateMissionProgress", body)

    def test_10_victory_defeat_and_turning_point_limit_are_unchanged(self):
        render = function_body("renderGame")
        self.assertIn("victory?'victory':'defeat'", render)
        self.assertIn("MISSION ${victory?'VICTORY':'DEFEAT'}", render)
        self.assertIn("Turning Point ${MAX_TURNING_POINTS} has ended.", render)
        self.assertIn("const MAX_TURNING_POINTS = 4;", APP)

    def test_11_application_displays_version_757(self):
        self.assertIn("const APP_VERSION = '8.6.12';", APP)
        self.assertIn("const APP_VERSION = '8.6.12';", WORKER)
        self.assertIn("V8.6.12", INDEX)
        self.assertTrue(README.startswith("# Tomb World Solo Guide v8.6.12"))
        self.assertIn("## v8.6.12", README)
        for asset in ("styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js", "event-effects.js", "app.js"):
            self.assertIn(f"{asset}?v=8.6.12", INDEX)

    def test_12_save_version_is_unchanged(self):
        persistence = (ROOT / "persistence.js").read_text()
        self.assertIn("const SAVE_VERSION = 3;", persistence)


if __name__ == "__main__":
    unittest.main()

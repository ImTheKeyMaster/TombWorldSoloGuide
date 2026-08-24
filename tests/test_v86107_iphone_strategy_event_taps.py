from versioning import CURRENT_APP_VERSION
import json
import subprocess
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
INDEX = (ROOT / "index.html").read_text()
README = (ROOT / "README.md").read_text()
WORKER = (ROOT / "service-worker.js").read_text()


def source(start, end):
    return APP[APP.index(start):APP.index(end, APP.index(start))]


def run_node(script):
    result = subprocess.run(["node", "-e", script], cwd=ROOT, text=True, capture_output=True)
    if result.returncode:
        raise AssertionError(result.stderr or result.stdout)
    return json.loads(result.stdout)


class IphoneStrategyEventTapTests(unittest.TestCase):
    def test_interactive_touches_never_suppress_click_synthesis(self):
        touch_setup = source("let lastTouchEnd=0;", "  const MAX_NPOS")
        result = run_node(f"""
let handler;
const document={{addEventListener:(name,callback,options)=>{{handler={{name,callback,options}};}}}};
{touch_setup}
const target=interactive=>({{closest:()=>interactive?{{}}:null}});
const event=interactive=>({{target:target(interactive),prevented:false,preventDefault(){{this.prevented=true;}}}});
const first=event(false), second=event(false), buttonAfterPage=event(true), rapidButton=event(true);
handler.callback(first); handler.callback(second); handler.callback(buttonAfterPage); handler.callback(rapidButton);
process.stdout.write(JSON.stringify({{
  eventName:handler.name,passive:handler.options.passive,
  first:first.prevented,second:second.prevented,
  buttonAfterPage:buttonAfterPage.prevented,rapidButton:rapidButton.prevented
}}));
""")
        self.assertEqual(result, {"eventName": "touchend", "passive": False, "first": False,
                                  "second": True, "buttonAfterPage": False, "rapidButton": False})

    def test_all_expected_interactive_controls_are_exempt(self):
        touch_setup = source("let lastTouchEnd=0;", "  const MAX_NPOS")
        for selector in ("button", "input", "select", "textarea", "a", "label", "summary",
                         '[role="button"]', '[role="link"]', '[role="checkbox"]',
                         '[role="radio"]', '[role="switch"]', '[role="tab"]', '[role="menuitem"]'):
            self.assertIn(selector, touch_setup)
        self.assertIn("e.target?.closest?", touch_setup)

    def test_maze_confirm_resolves_once_renders_immediately_and_logs_once(self):
        complete = source("async function completeCurrentEvent", "  function redrawCurrentEvent")
        resolve = source("async function resolveStrategyEvent", "  function randomReinforcement")
        result = run_node(f"""
const maze={{instanceId:'maze-1',definitionId:'maze-reforms',type:'tomb-world-event',title:'The Maze Reforms',
  text:'Close one breach.',execution:{{type:'maze-reforms'}},status:'drawn'}};
const state={{phase:'strategy',strategyStage:'summary',turningPoint:4,strategyData:{{event:maze,eventPending:true,eventIndex:0}},journal:[]}};
let saves=0,renders=0;
const currentEvent=()=>state.strategyData.event;
const log=text=>state.journal.push(text);
const beginCurrentEvent=()=>{{}};
const save=()=>{{saves++;}};
const render=()=>{{renders++;}};
{complete}
{resolve}
(async()=>{{
  await resolveStrategyEvent(); await resolveStrategyEvent();
  process.stdout.write(JSON.stringify({{status:maze.status,result:maze.result,pending:state.strategyData.eventPending,
    renders,saves,journal:state.journal,eventIndex:state.strategyData.eventIndex}}));
}})();
""")
        self.assertEqual(result["status"], "resolved")
        self.assertEqual(result["result"], "Breach and hatchway changes completed on the tabletop.")
        self.assertFalse(result["pending"])
        self.assertEqual(result["renders"], 1)
        self.assertEqual(result["saves"], 1)
        self.assertEqual(result["eventIndex"], 1)
        self.assertEqual(len(result["journal"]), 1)
        self.assertIn("Turning Point 4 · The Maze Reforms (standard rules)", result["journal"][0])

    def test_maze_controls_have_click_bindings_and_explicit_button_types(self):
        card = source("function strategyEventHtml", "  function activationTracker")
        bindings = source("function bindPlay", "  async function startTurningPoint")
        self.assertIn('<button type="button" class="btn primary" id="resolveStrategyEvent"', card)
        self.assertIn('<button type="button" class="btn secondary" id="redrawStrategyEvent"', card)
        self.assertIn("$('#resolveStrategyEvent')?.addEventListener('click'", bindings)
        self.assertIn("$('#redrawStrategyEvent')?.addEventListener('click'", bindings)
        self.assertIn("button.disabled=true", bindings)
        self.assertIn("if(!redrawCurrentEvent", bindings)

    def test_one_redraw_commits_one_replacement_and_preserves_reason(self):
        redraw = source("function redrawCurrentEvent", "  function processReinforcementStage")
        result = run_node(f"""
const maze={{instanceId:'maze-1',definitionId:'maze-reforms',title:'The Maze Reforms',status:'drawn',requiredBy:'standard'}};
const replacement={{instanceId:'next-1',definitionId:'dark-of-the-tomb',title:'Dark of the Tomb',status:'drawn'}};
const state={{turningPoint:4,strategyData:{{event:maze,events:[maze,replacement],eventIndex:0,eventPending:true}},eventState:{{transactions:{{}}}}}};
const eventRedrawsInProgress=new Set(); let draws=0,renders=0,logs=[];
const currentEvent=()=>state.strategyData.event;
const drawReplacementEvent=()=>{{draws++;return replacement;}};
const beginCurrentEvent=()=>{{}}; const log=text=>logs.push(text); const save=()=>{{}}; const render=()=>{{renders++;}};
const showModal=()=>{{}};
{redraw}
const first=redrawCurrentEvent('No breach or open hatchway could be changed.');
process.stdout.write(JSON.stringify({{first,draws,renders,status:maze.status,result:maze.result,
  current:state.strategyData.event.instanceId,transactions:Object.values(state.eventState.transactions),logs}}));
""")
        self.assertTrue(result["first"])
        self.assertEqual(result["draws"], 1)
        self.assertEqual(result["renders"], 1)
        self.assertEqual(result["status"], "redrawn")
        self.assertEqual(result["result"], "No breach or open hatchway could be changed.")
        self.assertEqual(result["current"], "next-1")
        self.assertEqual(len(result["transactions"]), 1)
        self.assertTrue(result["transactions"][0]["committed"])

    def test_menu_and_battle_record_navigation_only_changes_tab(self):
        render_game = source("function renderGame", "  function missionHudHtml")
        menu = source("function showGameMenu", "  function startNewGameSetup")
        self.assertIn("state.tab=button.dataset.gameView;save();", menu)
        self.assertIn("state.tab='play';save();render();", render_game)
        for mutation in ("eventPending=", ".status='resolved'", ".status='redrawn'", "redrawCurrentEvent(", "resolveStrategyEvent("):
            self.assertNotIn(mutation, menu)
            self.assertNotIn(mutation, render_game)

    def test_other_strategy_controls_remain_click_bound_and_mobile_layout_is_guarded(self):
        bindings = source("function bindPlay", "  async function startTurningPoint")
        for control in ("backStrategyActions", "continueStrategyReview", "backStrategyEvents", "continueStrategy"):
            self.assertIn(f"$('#{control}')?.addEventListener('click'", bindings)
        styles = (ROOT / "styles.css").read_text()
        self.assertIn("@media(max-width:390px)", styles.replace(" ", ""))
        self.assertIn("max-width:100%", styles.replace(" ", ""))

    def test_release_version_is_consistent_without_save_migration(self):
        self.assertTrue(README.startswith(f"# Tomb World Solo Guide v{CURRENT_APP_VERSION}\n\n## v{CURRENT_APP_VERSION}"))
        self.assertIn(f"const APP_VERSION = '{CURRENT_APP_VERSION}';", WORKER)
        self.assertIn(f"V{CURRENT_APP_VERSION}", INDEX)
        self.assertEqual(APP.count(f"const APP_VERSION = '{CURRENT_APP_VERSION}';"), 1)
        self.assertIn("const SAVE_VERSION = 3;", (ROOT / "persistence.js").read_text())


if __name__ == "__main__":
    unittest.main()

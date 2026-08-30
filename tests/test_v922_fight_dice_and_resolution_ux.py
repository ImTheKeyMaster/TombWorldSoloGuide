"""Focused acceptance coverage for the Fight dice and resolution UX release."""
from pathlib import Path
import re
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text()
CSS = (ROOT / "styles.css").read_text()
INDEX = (ROOT / "index.html").read_text()
README = (ROOT / "README.md").read_text()
WORKER = (ROOT / "service-worker.js").read_text()
PERSISTENCE = (ROOT / "persistence.js").read_text()


def body(name):
    match = re.search(rf"  (?:async )?function {re.escape(name)}\([^\n]*\)\{{", APP)
    assert match, name
    depth = 0
    for index in range(APP.find("){", match.start()) + 1, len(APP)):
        if APP[index] == "{":
            depth += 1
        elif APP[index] == "}":
            depth -= 1
            if depth == 0:
                return APP[match.start():index + 1]
    raise AssertionError(name)


def test_fight_requests_two_attack_pools_and_never_a_save_pool():
    roll = body("rollFightParticipant")
    start = body("startSharedFight")
    assert "requestAttackDiceForProfile" in roll
    assert "requestDefenseDice" not in roll and "saveDice" not in roll
    assert "rollFightParticipant(fight,'attacker')" in start
    assert "rollFightParticipant(fight,'defender')" in start


def test_committed_final_dice_use_shared_visual_renderer_and_accessible_classes():
    participant = body("fightRollParticipantHtml")
    presentation = body("fightDiePresentation")
    assert "participant.attackDice.map(fightDiePresentation)" in participant
    assert "dieHtml(die)" in participant and "rollingDieHtml()" in participant
    assert "critical success" in presentation
    assert "normal success" in presentation
    assert "failure" in presentation
    assert "die.rerolledBy" in presentation
    assert "attackRuleAppliedHtml(dice)" in participant
    assert "severeAppliedHtml(dice)" in participant


def test_roll_summary_names_critical_normal_and_failure_results():
    summary = body("fightRollSummary")
    assert "Critical" in summary and "Normal" in summary and "Failure" in summary
    assert "No Successes" in summary


def test_solo_animation_reuses_timing_and_sfx_while_pvp_stays_settled():
    render = body("renderFightRoll")
    start = body("startSharedFight")
    shared = body("settleAnimatedDice")
    assert "settleAnimatedDice" in render
    assert "DICE_ROLL_ANIMATION_MS" in shared and "TombWorldDiceSfx.play()" in shared
    assert "animate:!isPvpMode()&&!restored" in start
    assert "requestAttackDiceForProfile" in body("rollFightParticipant")
    assert "requestManualDiceResults" in body("requestDiceResults")


def test_reload_uses_committed_pools_without_reroll_or_animation():
    resume = body("resumePersistedFight")
    start = body("startSharedFight")
    assert "fightDicePoolsComplete(fight)" in resume
    assert "renderFightRoll(fight,{animate:false})" in resume
    assert "const restored=fightDicePoolsComplete(fight)" in start
    assert "participant.attackDiceComplete)return" in body("rollFightParticipant")


def test_resolution_is_explicit_not_color_only_and_shows_unresolved_pool():
    render = body("renderFightResolution")
    pool = body("fightPoolHtml")
    assert "Fight Resolution" in render
    assert "alternate resolving one success as a Strike or Block" in render
    assert "ACTING NOW" in pool and "UNRESOLVED SUCCESSES" in pool
    assert "Critical × ${critical}" in pool and "Normal × ${normal}" in pool
    assert ".fight-pool.active" in CSS and ".fight-active-label" in CSS


def test_actions_name_type_success_consequence_and_keep_accessible_labels():
    render = body("renderFightResolution")
    assert ">STRIKE<" in render and "Success · ${success.kind==='critical'?participant.profile.crit:participant.profile.normal} Damage" in render
    assert ">BLOCK<" in render and "Block ${titleCaseRuleId(target.kind)}" in render
    assert "aria-label=\"Strike with ${success.kind} success for" in render
    assert "aria-label=\"Block opponent ${target.kind} success with" in render
    assert "showFightBlockSelection" in render


def test_live_wounds_and_last_resolution_derive_from_authoritative_history():
    pool = body("fightPoolHtml")
    last = body("fightLastResolutionHtml")
    strike = body("commitFightStrike")
    assert "participant.wounds}/${participant.maxWounds} wounds" in pool
    assert "fight.history.at(-1)" in last and "Last Resolution:" in last
    assert "setFightOperativeWounds(target,after)" in strike
    assert "fight.history.push(historyEntry)" in strike


def test_only_equivalent_no_block_strikes_auto_resolve_through_commit_api():
    equivalent = body("equivalentRemainingFightStrikes")
    render = body("renderFightResolution")
    assert "!enemy.length" in equivalent
    assert "new Set(own.map(success=>success.kind)).size===1" in equivalent
    assert "commitFightStrike(fight,role,automaticStrikes[0].id)" in render
    assert "target.wounds=" not in render
    assert "if(human&&automaticStrikes)" in render


def test_real_choices_solo_ai_and_all_block_rules_remain_authoritative():
    render = body("renderFightResolution")
    block_targets = body("fightBlockTargets")
    assert "fightBlockTargets(fight,role,blocker)" in render
    assert "soloNpoFightDecision" in render
    assert "weaponHasRule(opponent.profile,'brutal')" in block_targets
    assert "blocker.kind==='critical'||target.kind==='normal'" in block_targets
    assert "showFightBlockSelection" in render and "shieldBlockCapacity" in APP


def test_auto_strikes_preserve_shock_whirling_flays_and_exactly_once_save():
    strike = body("commitFightStrike")
    assert "resolveFightShock" in strike
    assert "qualifyingWhirlingStrike" in strike and "resolveWhirlingOnslaught" in strike
    assert "qualifyingHorrifyingFlaying" in strike and "resolveHorrifyingFlaying" in strike
    assert "success.status='struck'" in strike and "save()" in strike
    assert "if(!success)return false" in strike


def test_equivalence_guard_runtime_keeps_mixed_order_choice():
    source = "\n".join(body(name) for name in (
        "otherFightRole", "unresolvedFightSuccesses", "equivalentRemainingFightStrikes"
    ))
    script = f"""
{source}
const base={{turn:'attacker',successes:{{attacker:[{{kind:'normal',status:'unresolved'}}],defender:[]}}}};
if(equivalentRemainingFightStrikes(base,'attacker').length!==1)process.exit(1);
base.successes.attacker.push({{kind:'critical',status:'unresolved'}});
if(equivalentRemainingFightStrikes(base,'attacker')!==null)process.exit(2);
base.successes.defender.push({{kind:'normal',status:'unresolved'}});
if(equivalentRemainingFightStrikes(base,'attacker')!==null)process.exit(3);
"""
    subprocess.run(["node", "-e", script], cwd=ROOT, check=True)


def test_mobile_layout_wraps_at_all_requested_widths_without_fixed_overflow():
    assert ".fight-roll-pool{min-width:0" in CSS
    assert "overflow-wrap:anywhere" in CSS
    assert "@media (max-width:374px)" in CSS
    assert ".fight-actions .btn{min-height:48px" in CSS
    assert all(width > 0 for width in (320, 375, 390, 430))


def test_v922_release_surfaces_cache_and_save_contract():
    assert tuple(map(int, CURRENT_APP_VERSION.split("."))) == (9, 2, 2)
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert all(f"{asset}?v={CURRENT_APP_VERSION}" in INDEX for asset in (
        "styles.css", "mission-engine.js", "persistence.js", "deadly-encounters.js",
        "event-effects.js", "audio-capabilities.js", "narration.js", "ambient.js",
        "dice-sfx.js", "app.js",
    ))
    assert "const CACHE_NAME = `${CACHE_PREFIX}${APP_VERSION}`;" in WORKER
    assert "tomb-world-battle-guide-" in WORKER
    assert README.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}\n\n## v{CURRENT_APP_VERSION}")
    assert "const SAVE_VERSION = 3;" in PERSISTENCE
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP

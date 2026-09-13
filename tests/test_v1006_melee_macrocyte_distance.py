from pathlib import Path

from versioning import CURRENT_APP_VERSION


ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
PERSISTENCE = (ROOT / "persistence.js").read_text(encoding="utf-8")


def source(start, end):
    return APP[APP.index(start) : APP.index(end, APP.index(start))]


def test_melee_does_not_render_a_distance_question_or_hidden_checkbox():
    fields = source("function aggressiveDefenseFields", "function aggressiveDefenseDamage")
    wizard = source("function showPendingPlayerAttackWizard", "function showPlayerCombatResolution")
    assert "attackType==='shoot'&&npo?.type==='Canoptek Macrocyte Warrior'" in fields
    assert "Attacker is within 2&quot; of this Macrocyte" in fields
    assert "Required only if this attack incapacitates the Macrocyte." in fields
    assert "aggressiveDefenseFields(target,attackType)" in wizard
    assert "display:none" not in fields
    assert "hidden" not in fields


def test_melee_records_and_carries_implicit_proximity():
    combat = source("function showPlayerCombatResolution", "async function previewPendingPlayerAttack")
    result = source("function buildFightResult", "function fightResultParticipantHtml")
    assert "const attackerWithinTwo=target.type==='Canoptek Macrocyte Warrior'" in combat
    assert "transaction.definitionAnswers.attackerWithinTwo=attackerWithinTwo" in combat
    assert "onComplete:onResolved,attackerWithinTwo" in combat
    assert "attackerWithinTwo:Boolean(fight.attackerWithinTwo)" in result


def test_resume_normalizes_legacy_melee_state_to_within_two():
    pending = source("function normalizePendingAttackResultLists", "function normalizeImpossiblePlayerCombat")
    fight = source("function normalizeFightState", "function otherFightRole")
    assert "npo.id===result.targetId&&npo.type==='Canoptek Macrocyte Warrior'" in pending
    assert "meleeCombatDraft={...normalized.meleeCombatDraft,attackerWithinTwo:true}" in pending
    assert "playerFightingMacrocyte" in fight
    assert "attackerWithinTwo:playerFightingMacrocyte?true:Boolean(fight.attackerWithinTwo)" in fight


def test_shooting_remains_player_confirmed_and_defaults_false():
    combat = source("function showPlayerCombatResolution", "async function previewPendingPlayerAttack")
    assert "Boolean($('#attackerWithinTwo')?.checked)||Boolean(result?.attackerWithinTwo)" in combat
    assert "transaction.definitionAnswers.attackerWithinTwo=attackerWithinTwo" in combat
    assert "diceDraft={attackDice:[],defenseDice:[],attackerWithinTwo:transaction.definitionAnswers.attackerWithinTwo" in combat


def test_non_macrocytes_do_not_receive_a_distance_question():
    fields = source("function aggressiveDefenseFields", "function aggressiveDefenseDamage")
    assert "npo?.type==='Canoptek Macrocyte Warrior'" in fields
    assert ": '';" in fields


def test_aggressive_defense_pipeline_and_interactions_are_unchanged():
    damage = source("function applyPendingPlayerDamage", "function showReanimationProtocolsResolution")
    trigger = "if(pending.after<=0&&!protectedForAction&&n.type==='Canoptek Macrocyte Warrior'&&pending.attackerWithinTwo&&!pending.aggressiveDefenseResolved)"
    assert trigger in damage
    assert "showIncapacitationOrderChoice" in damage
    assert "offerReanimateForPendingDamage" in damage
    assert damage.index("showIncapacitationOrderChoice") < damage.index(trigger)
    assert damage.index("offerReanimateForPendingDamage") < damage.index(trigger)
    assert damage.index(trigger) < damage.index("n.wounds=Math.max")
    resolver = source("async function showAggressiveDefenseResolution", "function showIncapacitationOrderChoice")
    assert "count:1,sides:3,title:'AGGRESSIVE DEFENCE'" in resolver
    assert "pending.aggressiveDefenseDamage=aggressiveDefenseDamage(retaliation.roll)" in resolver


def test_release_surfaces_and_save_schema_are_consistent():
    expected = CURRENT_APP_VERSION
    assert tuple(map(int, expected.split("."))) >= (10, 0, 6)
    assert README.startswith(f"# Tomb World Battle Guide v{expected}\n\n## v{expected}")
    assert f"const APP_VERSION = '{expected}';" in APP
    assert f"const APP_VERSION = '{expected}';" in WORKER
    assert f'<div class="version">V{expected}</div>' in INDEX
    assert f"analytics.js?release={expected}" in INDEX
    assert INDEX.count(f"?v={expected}") == 11
    assert "const SAVE_VERSION = 3;" in PERSISTENCE
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP

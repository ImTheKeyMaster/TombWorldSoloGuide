"""Keep the supplied Deathwatch portrait preview isolated from Standard Mode."""

import json
import subprocess
from pathlib import Path

from versioning import CURRENT_APP_VERSION

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
INDEX = (ROOT / "index.html").read_text(encoding="utf-8")
WORKER = (ROOT / "service-worker.js").read_text(encoding="utf-8")
README = (ROOT / "README.md").read_text(encoding="utf-8")
ASSETS = ROOT / "Assets/Images/TombUI/Deathwatch"
OPERATIVE_FILES = {
    "sergeant": "Deathwatch_sergeant.png",
    "aegis": "Deathwatch_aegis.png",
    "breacher": "Deathwatch_breacher.png",
    "blademaster": "Deathwatch_blademaster.png",
    "marksman": "Deathwatch_marksman.png",
    "demolisher": "Deathwatch_demolisher.png",
    "horde-slayer": "Deathwatch_horder-slayer.png",
    "headtaker": "Deathwatch_headtake.png",
    "gunner": "Deathwatch_gunner.png",
    "bombard": "Deathwatch_bombard.png",
    "disruptor": "Deathwatch_disruptor.png",
}


def run_node(script):
    result = subprocess.run(
        ["node", "-e", script], cwd=ROOT, capture_output=True, text=True, timeout=30
    )
    assert result.returncode == 0, result.stderr or result.stdout


def test_supplied_portraits_are_mapped_to_actual_deathwatch_ids_and_precached():
    team = json.loads((ROOT / "Player_Operatives/DeathWatch.json").read_text(encoding="utf-8"))
    assert set(OPERATIVE_FILES) == {operative["id"] for operative in team["operatives"]}
    for operative_id, filename in OPERATIVE_FILES.items():
        path = ASSETS / filename
        assert path.is_file(), f"Missing preview image for {operative_id}: {filename}"
        assert path.stat().st_size > 100_000, filename
        assert f"'./Assets/Images/TombUI/Deathwatch/{filename}'" in WORKER
        key = f"'{operative_id}'" if "-" in operative_id else operative_id
        assert f"{key}:'{filename}'" in APP
    assert "DeathwatchRoster/sergeant-fixed.svg" in WORKER
    assert "DeathwatchActivation/sergeant.webp" in WORKER
    assert "const CORE_PRECACHE_ASSETS=PRECACHE_ASSETS.filter" in WORKER
    assert "const OPTIONAL_PRECACHE_ASSETS=PRECACHE_ASSETS.filter" in WORKER


def test_standard_retains_original_portraits_and_experimental_skips_color_filter():
    run_node(r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const app=fs.readFileSync('app.js','utf8');
const begin=app.indexOf('const EXPERIMENTAL_DEATHWATCH_ROSTER_IMAGE_ROOT=');
const end=app.indexOf('  // User-photographed Death Korps cutouts',begin);
assert(begin>0&&end>begin);
const document={documentElement:{dataset:{ui:'tomb',experimental:'off'}}};
const pictures=[];
class Image{
 constructor(){this.decoding='';this.decodeCalls=0;this.onerror=null;pictures.push(this);}
 set src(value){this._src=value;}
 get src(){return this._src;}
 decode(){this.decodeCalls++;return Promise.resolve();}
}
const helpers=new Function('document','Image','escapeHtml',app.slice(begin,end)+
 '\nreturn {source:experimentalDeathwatchSuppliedPortraitImage,render:experimentalDeathwatchGreenPortraitSvg,legacyRoster:experimentalDeathwatchRosterImage,legacyActivation:experimentalDeathwatchActivationImage,warm:warmDeathwatchRosterImages,cache:warmedDeathwatchRosterImages};'
)(document,Image,x=>x);
const ids=['sergeant','aegis','breacher','blademaster','marksman','demolisher','horde-slayer','headtaker','gunner','bombard','disruptor'];
const expected={
 sergeant:'Deathwatch_sergeant.png',aegis:'Deathwatch_aegis.png',
 breacher:'Deathwatch_breacher.png',blademaster:'Deathwatch_blademaster.png',
 marksman:'Deathwatch_marksman.png',demolisher:'Deathwatch_demolisher.png',
 'horde-slayer':'Deathwatch_horder-slayer.png',
 headtaker:'Deathwatch_headtake.png',gunner:'Deathwatch_gunner.png',
 bombard:'Deathwatch_bombard.png',disruptor:'Deathwatch_disruptor.png'
};
assert.equal(helpers.source('sergeant'),'');
assert.equal(helpers.legacyRoster('sergeant'),'Assets/Images/TombUI/DeathwatchRoster/sergeant-fixed.svg');
assert.equal(helpers.legacyActivation('sergeant'),'Assets/Images/TombUI/DeathwatchActivation/sergeant.webp');
const standard=helpers.render('aegis','normalColor','test-svg');
assert(standard.includes('<filter id="normalColor"'), 'Standard loses its green-key SVG filter');
assert(standard.includes('DeathwatchActivation/aegis.webp'), 'Standard loses its old high-resolution photo');
assert(standard.includes('filter="url(#normalColor)"'), 'Standard color conversion no longer applies');
helpers.warm(['sergeant','aegis']);
assert.equal(pictures.length,2);
assert(pictures[0].src.endsWith('DeathwatchRoster/sergeant-fixed.svg'));
assert(pictures[1].src.endsWith('DeathwatchRoster/aegis.webp'));
document.documentElement.dataset.experimental='on';
for(const id of ids){
 const wanted='Assets/Images/TombUI/Deathwatch/'+expected[id];
 assert.equal(helpers.source(id),wanted,id);
 assert(fs.existsSync(wanted),'missing new portrait '+wanted);
 const artwork=helpers.render(id,'unusedFilter','tinted-svg');
 assert(artwork.includes('<image href="'+wanted+'"'),id);
 assert(artwork.includes('class="tinted-svg"'),id);
 assert(!artwork.includes('<filter')&&!artwork.includes('filter="'),id+' was recolored');
}
assert.equal(helpers.source('unknown'),'');
assert(helpers.render('unknown','fallbackFilter').includes('DeathwatchActivation/unknown.webp'));
helpers.warm(['sergeant','aegis','aegis']);
assert.equal(pictures.length,4,'Experimental loads only the two unique PNGs');
assert(pictures[2].src.endsWith('Deathwatch_sergeant.png'));
assert(pictures[3].src.endsWith('Deathwatch_aegis.png'));
assert(pictures.every(p=>p.decoding==='async'&&p.decodeCalls===1));
helpers.warm(['sergeant','aegis']);
assert.equal(pictures.length,4,'Experimental PNGs fetched repeatedly');
pictures[3].onerror();
assert(!helpers.cache.has(helpers.source('aegis')), 'Failed PNG download must be retryable');
helpers.warm(['aegis']);
assert.equal(pictures.length,5,'Failed PNG was not retried');
document.documentElement.dataset.experimental='off';
const standardAgain=helpers.render('sergeant','originalFilter','test-svg');
assert(standardAgain.includes('DeathwatchActivation/sergeant.webp'));
assert(standardAgain.includes('filter="url(#originalFilter)"'));
helpers.warm(['sergeant','aegis']);
assert.equal(pictures.length,5,'Switching back to Standard reloaded cached originals');
document.documentElement.dataset.ui='classic';
helpers.warm(['gunner']);
assert.equal(pictures.length,5,'Classic UI must not trigger a portrait warmup');
""")


def test_preview_reaches_activation_roster_combat_but_not_death_korps():
    activation = APP[
        APP.index("  function renderHumanPlayerActionPicker()")
        : APP.index("  function playerSequentialStage(", APP.index("  function renderHumanPlayerActionPicker()"))
    ]
    assert "portraitUrl:document.documentElement.dataset.ui==='tomb'" in activation
    assert "?experimentalDeathwatchActivationImage(activation.operativeId):''" in activation
    assert "portraitMarkup:document.documentElement.dataset.ui==='tomb'" in activation
    assert "selectedPlayerTeamName().toLowerCase()==='deathwatch'&&experimentalDeathwatchSuppliedPortraitImage(activation.operativeId)" in activation
    assert 'href="${escapeHtml(experimentalDeathwatchSuppliedPortraitImage(activation.operativeId))}"' in activation
    assert "selectedPlayerTeamName().toLowerCase()==='death korps'&&deathKorpsPortraitImage(activation.operativeId)" in activation
    assert "const resolvedPortraitMarkup=portraitMarkup||(portraitUrl?" in APP

    rail = APP[APP.index("  function playerRosterPortraitMarkup(") : APP.index("  function usesPlayerPortraitRail(", APP.index("  function playerRosterPortraitMarkup("))]
    assert "return experimentalDeathwatchGreenPortraitSvg(id,filterId,svgClass)" in rail
    assert "deathKorpsPortraitImage(id)" in rail
    assert "detailImage.innerHTML=playerRosterPortraitMarkup(" in APP
    assert "experimentalDeathwatchGreenPortraitSvg(id,'blastResultPlayerPortrait'" in APP
    assert "experimentalDeathwatchGreenPortraitSvg(participant.id,`fightPortraitDeathwatch-" in APP
    assert "if(data.teamName?.toLowerCase()==='deathwatch')warmDeathwatchRosterImages(data.operatives.map(operative=>operative.id));" in APP
    assert "const src=experimentalDeathwatchSuppliedPortraitImage(id)||experimentalDeathwatchRosterImage(id);" in APP
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP


def test_experimental_toggle_version_and_offline_app_remain_intact():
    assert "if(document.documentElement.dataset.experimental!=='on')return '';" in APP
    assert '<html lang="en" data-ui="tomb" data-experimental="off">' in INDEX
    assert "document.documentElement.dataset.experimental=enabled?'on':'off';" in APP
    assert "Preview the supplied green Deathwatch portraits in Experimental Mode" in INDEX
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in WORKER
    assert f'<div class="version">V{CURRENT_APP_VERSION}</div>' in INDEX
    assert README.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}\n\n## v{CURRENT_APP_VERSION}")
    for filename in ("app.js", "styles.css", "persistence.js"):
        assert f"{filename}?v={CURRENT_APP_VERSION}" in INDEX
    assert "function warmDeathKorpsPortraitImages(" in APP
    assert "function resumeCombatAfterWeaponRuleCheck(" in APP
    assert "function advanceMultiTargetAttackSequence(" in APP

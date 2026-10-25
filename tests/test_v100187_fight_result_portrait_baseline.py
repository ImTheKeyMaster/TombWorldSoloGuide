"""Fight Result shows full miniatures with matching base lines and unobscured text."""

from pathlib import Path
import re
import subprocess

from versioning import CURRENT_APP_VERSION

ROOT=Path(__file__).resolve().parents[1]
CSS=(ROOT/"styles.css").read_text(encoding="utf-8")
APP=(ROOT/"app.js").read_text(encoding="utf-8")


def rule(selector):
    matches=re.findall(re.escape(selector)+r"\s*\{([^}]*)\}",CSS)
    assert matches,selector
    return matches[-1]


def test_both_fight_result_portraits_bottom_align_and_fit_whole_figure():
    frame=rule('html[data-ui="tomb"] .fight-result-card.has-fight-portrait .fight-portrait')
    photo=rule('html[data-ui="tomb"] .fight-result-card.has-fight-portrait .fight-portrait .fight-portrait-artwork')
    assert "inset:0 0 0 auto" in frame
    assert "height:100%" in frame
    assert "width:min(100%,190px)" in frame
    assert "opacity:.4" in frame
    assert "mask-image:linear-gradient" in frame
    assert "width:100%" in photo and "height:100%" in photo
    assert "max-height:100%" in photo
    assert "object-fit:contain" in photo
    assert "object-position:center bottom" in photo
    assert "transform:none" in photo
    assert ".death-korps-portrait" not in CSS.split("/* v10.0.187:",1)[1].split("/* v10.0.189:",1)[0]
    assert ".experimental-necron-framed-svg" not in CSS.split("/* v10.0.187:",1)[1].split("/* v10.0.189:",1)[0]


def test_fight_result_photos_stay_behind_text_without_changing_result_content():
    css=CSS.split("/* v10.0.187:",1)[0]
    assert '.fight-result-card.has-fight-portrait>*:not(.fight-portrait)' in css
    assert "z-index:1" in css
    assert '.fight-result-card.has-fight-portrait>h3' in css
    assert '.fight-result-card.has-fight-portrait dl' in css
    script=r"""
const assert=require('node:assert/strict'),fs=require('node:fs');
const source=fs.readFileSync('app.js','utf8');
const first=source.indexOf('  function fightResultParticipantHtml(');
const end=source.indexOf('  function acknowledgeFightResult(',first);
assert(first>0&&end>first);
const ctx={
  fightParticipantPortrait:(participant,role)=>
    '<span class="fight-portrait fight-portrait-'+role+'"><img class="fight-portrait-artwork '+(role==='attacker'?'death-korps-portrait-photo':'experimental-necron-framed-svg')+'" src="art.png" alt=""></span>',
  escapeHtml:s=>String(s),
  document:{documentElement:{dataset:{ui:'tomb'}}}
};
const draw=new Function('ctx','with(ctx){'+source.slice(first,end)+
  '\nreturn fightResultParticipantHtml;}')(ctx);
for(const role of ['attacker','defender']){
  const html=draw({name:role==='attacker'?'Trooper 2':'Canoptek Macrocyte Warrior 2',
    damageDealt:3,before:7,after:4,incapacitated:false},role);
  assert.match(html,/fight-result-card has-fight-portrait/);
  assert.match(html,/fight-portrait-artwork/);
  assert.match(html,/Damage Dealt/);
  assert.match(html,/Wounds/);
  assert.match(html,/7/);
  assert.match(html,/4/);
}
"""
    result=subprocess.run(["node","-e",script],cwd=ROOT,
                          text=True,capture_output=True,timeout=30)
    assert result.returncode==0,result.stderr or result.stdout


def test_non_result_framing_and_version_unchanged():
    new=CSS.split("/* v10.0.187:",1)[1].split("/* v10.0.190:",1)[0]
    for forbidden in (".experimental-fight-pool",".fight-roll-pool",".human-activation-shell",
                      ".experimental-activation-portrait",".experimental-necron-activation"):
        assert forbidden not in new
    assert 'width:135%' in CSS  # Existing smaller Death Korps Activation framing
    assert '/* v10.0.186: Fight Resolution miniature bases' in CSS
    html=(ROOT/"index.html").read_text(encoding="utf-8")
    worker=(ROOT/"service-worker.js").read_text(encoding="utf-8")
    readme=(ROOT/"README.md").read_text(encoding="utf-8")
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in APP
    assert f"const APP_VERSION = '{CURRENT_APP_VERSION}';" in worker
    assert f'V{CURRENT_APP_VERSION}' in html
    assert f'app.js?v={CURRENT_APP_VERSION}' in html
    assert f'styles.css?v={CURRENT_APP_VERSION}' in html
    assert readme.startswith(f"# Tomb World Battle Guide v{CURRENT_APP_VERSION}")
    assert "const STORAGE_KEY = 'tombWorldBattleGuide.v1';" in APP

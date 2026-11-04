"""Every Aggressive Defence operative uses the same enlarged, uncropped portrait slot."""
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
APP = (ROOT / "app.js").read_text(encoding="utf-8")
CSS = (ROOT / "styles.css").read_text(encoding="utf-8")


def source(start, end):
    return APP[APP.index(start):APP.index(end, APP.index(start))]


def test_all_supported_player_operative_types_use_the_shared_portrait():
    rendering=source("function fightParticipantPortrait", "function scaleFightPortraits")
    outcome=source("function experimentalAggressiveDefenseOutcome", "function aggressiveDefenseRollHtml")
    assert "selectedPlayerTeamName().toLowerCase()==='deathwatch'" in rendering
    assert "deathwatchPortraitSvg(participant.id,'fight-portrait-artwork')" in rendering
    assert "selectedPlayerTeamName().toLowerCase()==='death korps'" in rendering
    assert "deathKorpsCombatPortraitSvg(participant.id,'fight-portrait-artwork')" in rendering
    assert "fightParticipantPortrait({side:'player',id:operativeId},'aggressive-defence')" in outcome
    assert 'class="aggressive-defense-operative-portrait"' in outcome
    assert "operativeId==='bombard'" not in outcome

    # Exercise the actual shared portrait renderer with representatives of both teams.
    script="""
      const assert=require('node:assert/strict');
      let team='Deathwatch';
      const state={roster:[]};
      const selectedPlayerTeamName=()=>team;
      const playerDefinition=id=>({baseSize:32});
      const deathwatchPortraitSvg=(id,klass)=>'<img class="'+klass+'" data-operative="'+id+'">';
      const deathKorpsCombatPortraitSvg=(id,klass)=>'<img class="'+klass+'" data-operative="'+id+'">';
      const deathwatchPortraitImage=id=>'Deathwatch_'+id+'.png';
      const deathKorpsPortraitImage=id=>'Death_Korps_'+id+'.png';
      const experimentalNecronPortraitSvg=()=>null;
    """ + rendering + """
      for(const faction of ['Deathwatch','Death Korps']){
        team=faction;
        for(const id of ['bombard','gunner','sergeant','trooper-1','watchmaster']){
          const html=fightParticipantPortrait({side:'player',id},'aggressive-defence');
          assert(html.includes('fight-portrait-artwork'),faction+':'+id);
          assert(html.includes('aggressive-defence'),faction+':'+id);
          assert(html.includes('data-operative="'+id+'"'),faction+':'+id);
        }
      }
    """
    result=subprocess.run(["node","-e",script],cwd=ROOT,capture_output=True,text=True)
    assert result.returncode==0,result.stderr


def test_portrait_fills_result_card_height_without_distortion_or_clipping():
    css=CSS[CSS.index("/* Experimental Aggressive Defence:"):CSS.index("@media(max-width:600px)",CSS.index("/* Experimental Aggressive Defence:"))]
    assert "min-height:184px" in css
    assert "flex:0 0 min(46%,168px)" in css
    assert "min-height:176px;overflow:hidden;align-self:stretch" in css
    assert "position:relative" in css
    assert "position:absolute;inset:auto 0 0" in css
    assert "object-fit:contain;object-position:center bottom" in css
    assert "img.fight-portrait-artwork" in css
    assert ".aggressive-defense-operative-portrait{width:72px;height:100px}" not in css
    assert "flex-basis:min(44%,145px)" in css
    assert "min-height:164px" in css
    assert ".aggressive-defense-operative-details{display:grid;flex:1" in css
    assert "opacity:.86" in css
    # Same CSS applies to both factions, never a particular operative or portrait file.
    for forbidden in ("bombard", "sergeant", "trooper", "Deathwatch_", "Death_Korps_", ".deathwatch-portrait", ".death-korps-portrait"):
        assert forbidden not in css


def test_unchanged_damage_commit_and_shared_solo_tomb_gate():
    damage=source("async function showAggressiveDefenseResolution", "function showIncapacitationOrderChoice")
    assert "const usePortraitResult=!isPvpMode()&&document.documentElement.dataset.ui==='tomb';" in damage
    assert "if(aggressiveDamage>0&&!pending.aggressiveDefenseDamageApplied)" in damage
    assert "pending.aggressiveDefenseResolved=true" in damage

(() => {
  'use strict';

  const STORAGE_KEY = 'tombWorldSoloGuide.v1';
  const APP_VERSION = '2.2.6';

let lastTouchEnd=0;
document.addEventListener('touchend',function(e){const now=Date.now();if(now-lastTouchEnd<=300){e.preventDefault();}lastTouchEnd=now;},{passive:false});
  const MAX_NPOS = 10;
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
  const app = $('#app');
  const gameMenuBtn = $('#gameMenuBtn');
  const modal = $('#modal');
  const modalBody = $('#modalBody');
  const toast = $('#toast');
  const importInput = $('#importInput');

  let missionManifest=null;
  async function loadMissionPack(){
    const manifestResponse=await fetch('Missions/manifest.json',{cache:'no-store'});
    if(!manifestResponse.ok)throw new Error(`Unable to load Missions/manifest.json (${manifestResponse.status})`);
    missionManifest=await manifestResponse.json();
    if(!Array.isArray(missionManifest.missions)||!missionManifest.missions.length)throw new Error('Mission manifest has no missions.');
    const loaded=await Promise.all(missionManifest.missions.map(async entry=>{
      const response=await fetch(`Missions/${entry.file}`,{cache:'no-store'});
      if(!response.ok)throw new Error(`Unable to load ${entry.file} (${response.status})`);
      return response.json();
    }));
    missions=loaded.sort((a,b)=>String(a.number).localeCompare(String(b.number)));
    maps=Object.fromEntries(missions.map(m=>[m.id,m.map||{walls:[],hatches:[],markers:[]}]));
  }

  let playerManifest=null;
  let playerTeamData=null;
  async function loadPlayerManifest(){
    const response=await fetch('Player_Operatives/manifest.json',{cache:'no-store'});
    if(!response.ok)throw new Error(`Unable to load manifest.json (${response.status})`);
    const data=await response.json();
    if(!Array.isArray(data.teams)||!data.teams.length)throw new Error('manifest.json has no Kill Teams.');
    playerManifest=data;
    return data;
  }
  function playerTeamEntry(teamId=state.playerTeamId){
    return playerManifest?.teams?.find(team=>team.id===teamId)||null;
  }
  async function loadPlayerTeamData(teamId=state.playerTeamId){
    const entry=playerTeamEntry(teamId);
    if(!entry)throw new Error(`Kill Team "${teamId||'unknown'}" is not listed in manifest.json.`);
    const response=await fetch(`Player_Operatives/${entry.file}`,{cache:'no-store'});
    if(!response.ok)throw new Error(`Unable to load ${entry.file} (${response.status})`);
    const data=await response.json();
    if(!Array.isArray(data.operatives)||!data.operatives.length)throw new Error(`${entry.file} has no operatives.`);
    playerTeamData=data;
    state.playerTeamId=entry.id;
    state.playerTeamFile=entry.file;
    return data;
  }
  function playerDefinition(id){return playerTeamData?.operatives?.find(o=>o.id===id)||null;}
  function selectedPlayerOperatives(){return (state.playerRoster||[]).map(playerDefinition).filter(Boolean);}
  function playerName(id){return playerDefinition(id)?.name||String(id);}

  let missions=[];
  let maps={};

  const profiles = {
    'Necron Warrior': {behavior:'Marksman',wounds:10,save:3,attack:{dice:4,hit:4,normal:3,crit:4}},
    'Canoptek Scarab Swarm': {behavior:'Brawler',wounds:8,save:4,attack:{dice:5,hit:4,normal:2,crit:3}},
    'Canoptek Macrocyte': {behavior:'Sentinel',wounds:9,save:4,attack:{dice:4,hit:3,normal:3,crit:4}},
    'Canoptek Tomb Crawler': {behavior:'Guardian',wounds:12,save:3,attack:{dice:4,hit:3,normal:4,crit:5}}
  };

  const events = [
    ['Awakened Warrior','Add one ready Necron Warrior at a suitable tomb entry point.'],
    ['A Chittering Drone','Add a Scarab Swarm, or fully heal one if it is already active.'],
    ['Living Metal Flux','Each wounded NPO regains D3+2 wounds.'],
    ['The Maze Reforms','Close one breach and up to D3 open hatchways where possible.'],
    ['Stirrings of Horror','Increase Threat by 1.'],
    ['Countertemporal Shifting','NPOs partially resist high-damage attacks this Turning Point.']
  ];

  const initialState = () => ({
    version:'1.4.0c', screen:'home', tab:'play', setupStep:0, missionId:null,
    setupChecks:[], roster:[], playerTeamId:'', playerTeamFile:'', playerRoster:[], playerCount:0, playerReady:0, playerDeployed:false, turningPoint:0,
    threat:0, initiative:'player', phase:'setup', nextSide:'player', tracker:0,
    activeNpoId:null, journal:[], lastActivation:null, newIds:[], completed:false,
    strategyStage:null, strategyData:null, activationNumber:0, playerActivated:0, npoActivated:0,
    activationHistory:[], playerActivatedIds:[], playerCasualtyIds:[], reinforcementEntry:'Nearest valid entry point',
    gradeMilestone:null, tpStartThreat:0, tpStartGrade:0, tpStartDestroyedNpos:0, tpStartPlayerCasualties:0,
    npoAttackTargetId:null,
    npoAttackSummary:null
  });

  let state = normalizeState(load() || initialState());
  let lastRenderedStepKey = null;
  let threatAdjustOpen = false;

  function save(){ state.version=APP_VERSION; localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); }
  function load(){ try{return JSON.parse(localStorage.getItem(STORAGE_KEY));}catch{return null;} }
  function normalizeState(raw){
    const base=initialState(), merged={...base,...raw};
    merged.roster=Array.isArray(raw?.roster)?raw.roster:[];
    merged.journal=Array.isArray(raw?.journal)?raw.journal:[];
    merged.newIds=Array.isArray(raw?.newIds)?raw.newIds:[];
    merged.activationHistory=Array.isArray(raw?.activationHistory)?raw.activationHistory:[];
    merged.playerActivatedIds=Array.isArray(raw?.playerActivatedIds)?raw.playerActivatedIds:[];
    merged.playerCasualtyIds=Array.isArray(raw?.playerCasualtyIds)?raw.playerCasualtyIds:[];
    merged.playerRoster=Array.isArray(raw?.playerRoster)?raw.playerRoster:[];
    merged.playerTeamId=raw?.playerTeamId||'';
    merged.playerCount=merged.playerRoster.length;
    return merged;
  }
  function mission(){ return missions.find(m => m.id === state.missionId) || missions[0]; }
  function missionSetup(m=mission()){return m?.startingNpos?.formula||'0';}
  function missionTracker(m=mission()){return m?.tracker?.label||'Mission progress';}
  function missionTrackerMax(m=mission()){return Number(m?.tracker?.max||0);}
  function missionSpecial(m=mission()){return (m?.rules||[]).map(rule=>`${rule.name}: ${rule.summary}`).join(' ');}
  function missionFirstInitiative(m=mission()){return m?.firstTurningPointInitiative||'player';}

  function roll(sides=6){ return Math.floor(Math.random()*sides)+1; }
  function rollD3(){ return roll(3); }
  function uid(){ return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2,7)}`; }
  function activeNpos(){ return state.roster.filter(n => n.wounds > 0); }
  function readyNpos(){ return activeNpos().filter(n => n.ready); }
  function playerOperativesRemaining(){
    const casualties=new Set(state.playerCasualtyIds||[]);
    const activated=new Set(state.playerActivatedIds||[]);
    return (state.playerRoster||[]).filter(id=>!casualties.has(id)&&!activated.has(id)).length;
  }
  function destroyedNpoCount(){ return state.roster.filter(n=>n.wounds<=0).length; }
  function eligibleNpoAttackTargets(){
    const casualties=new Set(state.playerCasualtyIds||[]);
    return (state.playerRoster||[]).filter(id=>!casualties.has(id));
  }
  function selectedNpoAttackTarget(){
    return playerDefinition(state.npoAttackTargetId);
  }

  function setNextActivation(preferredSide){
    const playerRemaining=playerOperativesRemaining();
    const npoRemaining=readyNpos().length;

    if(playerRemaining<=0 && npoRemaining<=0){
      state.nextSide=null;
      state.phase='end';
      return null;
    }
    if(playerRemaining<=0){
      state.nextSide='npo';
      return 'npo';
    }
    if(npoRemaining<=0){
      state.nextSide='player';
      return 'player';
    }

    state.nextSide=preferredSide==='npo'?'npo':'player';
    return state.nextSide;
  }

  function advanceAfterActivation(completedSide){
    return setNextActivation(completedSide==='player'?'npo':'player');
  }

  function threatGrade(){ return state.threat === 0 ? 0 : state.threat <= 5 ? 1 : state.threat <= 10 ? 2 : 3; }
  function threatLabel(){ return ['Dormant','Stirring','Awakened','Overrun'][threatGrade()]; }
  function threatToNext(){ const g=threatGrade(); if(g===3)return 0; return [1,6,11][g]-state.threat; }
  function log(text){ state.journal.unshift({time:new Date().toISOString(),text}); state.journal=state.journal.slice(0,150); }
  function setThreat(amount,reason){
    const before=state.threat;
    const beforeGrade=threatGrade();
    state.threat=Math.max(0,Math.min(15,state.threat+amount));
    const afterGrade=threatGrade();
    if(state.threat!==before) log(`Threat ${before} → ${state.threat}: ${reason}`);
    if(afterGrade>beforeGrade){
      state.gradeMilestone={grade:afterGrade,threat:state.threat,label:threatLabel()};
      log(`Threat reached Grade ${afterGrade}: ${threatLabel()}.`);
    }
  }
  function escapeHtml(s){ return String(s).replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c])); }

  function generateRoster(){
    const m=mission(); let count=0, formula='0';
    if(missionSetup(m)==='2D3+3'){ const a=rollD3(),b=rollD3(); count=a+b+3; formula=`${a} + ${b} + 3 = ${count}`; }
    if(missionSetup(m)==='D3+6'){ const a=rollD3(); count=a+6; formula=`${a} + 6 = ${count}`; }
    const table=['Canoptek Scarab Swarm','Canoptek Scarab Swarm','Canoptek Macrocyte','Necron Warrior','Necron Warrior','Necron Warrior','Necron Warrior','Necron Warrior','Canoptek Tomb Crawler','Canoptek Tomb Crawler','Necron Warrior'];
    state.roster=[];
    for(let i=0;i<count;i++){
      const type=table[Math.min(table.length-1,Math.max(0,roll(6)+roll(6)-2))];
      const p=profiles[type]; state.roster.push({id:uid(),name:`${type} ${i+1}`,type,behavior:p.behavior,maxWounds:p.wounds,wounds:p.wounds,save:p.save,attack:{...p.attack},ready:false,deployed:false});
    }
    state.newIds=[]; log(`${m.name}: generated ${count} starting NPOs (${formula}).`); return {count,formula};
  }

  function render(){
    const currentStepKey = [
      state.screen,
      state.setupStep ?? '',
      state.tab ?? '',
      state.phase ?? '',
      state.turningPoint ?? '',
      state.nextSide ?? '',
      state.activationNumber ?? ''
    ].join(':');
    const movedToNewStep = lastRenderedStepKey !== null && currentStepKey !== lastRenderedStepKey;
    lastRenderedStepKey = currentStepKey;

    gameMenuBtn.hidden = state.screen !== 'game';
    if(state.screen==='home') renderHome();
    else if(state.screen==='help') renderHowItWorks();
    else if(state.screen==='setup') renderSetup();
    else renderGame();
    bindCommon();

    if(movedToNewStep){
      requestAnimationFrame(()=>{
        window.scrollTo({top:0,left:0,behavior:'auto'});
        document.documentElement.scrollTop=0;
        document.body.scrollTop=0;
      });
    }
  }

  function guideInstructionsHtml(full=false){
    const overview=`<section class="help-section">
      <h3>What the Guide does</h3>
      <p>Tomb World Solo Guide walks you through setup, Turning Points, alternating Player and NPO activations, Threat, reinforcements, combat, and the battle record. You still move models, measure distances, determine line of sight, and apply any operative-specific rules on the tabletop.</p>
    </section>`;

    const flow=`<section class="help-section">
      <h3>Game flow</h3>
      <ol class="guide-flow-list">
        <li><strong>Set up the mission</strong><span>Choose a mission, build the killzone, generate the starting NPO roster, and deploy both sides.</span></li>
        <li><strong>Prepare the Turning Point</strong><span>The Guide readies operatives, evaluates Threat Grade, generates reinforcements, checks events, and resolves initiative.</span></li>
        <li><strong>Alternate activations</strong><span>The side with initiative activates first. Player and NPO activations then alternate until one side runs out of ready operatives.</span></li>
        <li><strong>End the Turning Point</strong><span>Score mission progress, resolve end-of-turn effects, and begin the next Turning Point.</span></li>
      </ol>
    </section>`;

    const ai=`<section class="help-section ai-help-section">
      <h3>How the NPO AI decides</h3>
      <div class="ai-step-grid">
        <article><span>1</span><div><strong>Queue the NPO</strong><p>The Guide identifies the next ready NPO. Every battlefield question applies only to that operative.</p></div></article>
        <article><span>2</span><div><strong>Follow its behavior</strong><p><b>Brawler:</b> close distance, Charge, and Fight. <b>Marksman:</b> seek a legal shot and useful cover. <b>Sentinel:</b> engage nearby threats first, then act like a Marksman.</p></div></article>
        <article><span>3</span><div><strong>Evaluate the battlefield</strong><p>Your answers tell the Guide whether the NPO can Fight, Charge, Shoot, contest an objective, pursue a wounded target, operate a hatch, or reposition.</p></div></article>
        <article><span>4</span><div><strong>Choose the most dangerous legal option</strong><p>When several choices are legal, the AI favors damage, mission denial, and pressure against the Player.</p></div></article>
        <article><span>5</span><div><strong>Break true ties</strong><p>If two options remain genuinely equal, choose the result most favorable to the Tomb World. Randomize only when they are still indistinguishable.</p></div></article>
        <article><span>6</span><div><strong>Resolve it on the tabletop</strong><p>The Guide gives the action sequence, target priority, stance, and attack dice. You carry out movement, measuring, visibility, and special rules.</p></div></article>
      </div>
      <div class="golden-rule"><strong>Golden rule</strong><span>If the Guide cannot distinguish between two legal choices, use the option most favorable to the NPOs.</span></div>
    </section>`;

    const combat=`<section class="help-section">
      <h3>Player activation and combat</h3>
      <p>Select a remaining Player operative, set its APL, choose legal actions, and press <strong>Complete Activation</strong>. Selected Shooting or Melee attacks are then resolved. Damage remains pending until you confirm the entire activation, so canceling or going back does not alter NPO wounds.</p>
    </section>`;

    const quick=`<section class="help-section quick-reference-grid">
      <article><h4>Player</h4><p>Your solo kill-team operatives.</p></article>
      <article><h4>NPO</h4><p>A non-player operative controlled by the Guide.</p></article>
      <article><h4>APL</h4><p>The number of action points an operative may spend during its activation.</p></article>
      <article><h4>THREAT LEVEL</h4><p>A 0–15 alert meter. Higher grades generate more reinforcements and events.</p></article>
      <article><h4>Ready</h4><p>The operative can still activate during this Turning Point.</p></article>
      <article><h4>Expended</h4><p>The operative has activated or is otherwise unavailable.</p></article>
    </section>`;

    if(full) return overview+flow+ai+combat+quick;
    return ai+quick;
  }

  function renderHome(){
    const canContinue=Boolean(load()?.missionId && load()?.screen==='game');
    app.innerHTML=`<section class="hero-card">
      <img class="hero-symbol" src="Assets/icon.svg" alt="">
      <p class="eyebrow">A STEP-BY-STEP DIGITAL GAME MASTER</p>
      <h2>Enter the Tomb</h2>
      <p>Choose a mission, build the board, deploy the correct NPO roster, and follow one clear next action through every Turning Point.</p>
      <div class="button-row">
        <button class="btn primary" id="newGameBtn">New Game</button>
        <button class="btn secondary" id="continueBtn" ${canContinue?'':'disabled'}>Continue Game</button>
        <button class="btn ghost" id="homeHelpBtn">How It Works</button>
      </div>
    </section>`;
    $('#newGameBtn').onclick=()=>{ state=initialState(); state.screen='setup'; state.setupStep=0; save(); render(); };
    $('#continueBtn').onclick=()=>{ const saved=load(); if(saved){state=saved;state.screen='game';render();} };
    $('#homeHelpBtn').onclick=()=>{
      state.screen='help';
      render();
      window.scrollTo({top:0,left:0,behavior:'auto'});
    };
  }


  function renderHowItWorks(){
    app.innerHTML=`<section class="how-it-works-screen">
      <div class="screen-toolbar">
        <button class="btn ghost compact" id="howItWorksBackBtn" type="button" aria-label="Return to Home">← Back</button>
        <span class="screen-version">v${APP_VERSION}</span>
      </div>
      <header class="screen-heading">
        <p class="eyebrow">TOMB WORLD SOLO GUIDE</p>
        <h2>How It Works</h2>
        <p>Use the Guide as a digital game master while you handle models, measuring, visibility, and operative-specific rules on the tabletop.</p>
      </header>
      <div class="how-it-works-content">
        ${guideInstructionsHtml(true)}
      </div>
      <div class="wizard-actions how-it-works-footer">
        <button class="btn primary" id="howItWorksDoneBtn" type="button">Back to Home</button>
      </div>
    </section>`;

    const goHome=()=>{
      state.screen='home';
      render();
      window.scrollTo({top:0,left:0,behavior:'auto'});
    };
    $('#howItWorksBackBtn').onclick=goHome;
    $('#howItWorksDoneBtn').onclick=goHome;
  }

  function hasMultiplePlayerTeams(){return (playerManifest?.teams?.length||0)>1;}
  function renderTeamSelection(){
    const cards=(playerManifest?.teams||[]).map(team=>`<button type="button" class="team-select-card" data-player-team="${escapeHtml(team.id)}">
      <div><strong>${escapeHtml(team.name)}</strong><small>${escapeHtml(team.faction||'Kill Team')}</small></div>
      <p>${escapeHtml(team.description||'')}</p>
    </button>`).join('');
    app.innerHTML=`<div class="wizard-shell"><div class="progress-head"><div><p class="eyebrow">NEW GAME SETUP</p><h2>Choose Kill Team</h2><p>Select the player-controlled Kill Team for this battle.</p></div></div><section class="wizard-card"><div class="team-select-grid">${cards}</div><div class="wizard-actions"><button class="btn ghost" id="teamSelectHome">Back</button></div></section></div>`;
    $('#teamSelectHome').onclick=()=>{state.screen='home';save();render();};
    $$('[data-player-team]').forEach(button=>button.onclick=async()=>{
      try{
        state.playerTeamId=button.dataset.playerTeam;
        state.playerRoster=[];
        state.playerCount=0;
        state.playerReady=0;
        state.playerCasualtyIds=[];
        state.playerActivatedIds=[];
        state.playerDeployed=false;
        await loadPlayerTeamData(state.playerTeamId);
        save();
        render();
      }catch(error){
        console.error(error);
        showToast(error.message);
      }
    });
  }

  const setupTitles=['Choose Mission','Build the Killzone','Generate NPO Roster','Deploy NPOs','Build Player Roster','Ready to Begin'];
  function renderSetup(){
    if(hasMultiplePlayerTeams()&&!state.playerTeamId){renderTeamSelection();return;}
    const step=state.setupStep;
    app.innerHTML=`<div class="wizard-shell"><div class="progress-head"><div><p class="eyebrow">NEW GAME SETUP</p><h2>${setupTitles[step]}</h2><p>${setupSubtitle(step)}</p></div><div class="step-count">${step+1} / 6</div></div><div class="progress-bar"><span style="width:${((step+1)/6)*100}%"></span></div><section class="wizard-card">${setupContent(step)}</section></div>`;
    bindSetup(step);
  }
  function setupSubtitle(step){return [
    'Select the mission the Guide will run.',
    'Follow the board checklist before deploying models.',
    'The Guide uses the mission’s required starting formula.',
    'Place each generated NPO in the mission’s indicated areas.',
    'Tell the Guide how many operatives are in your solo kill team.',
    'Review the setup, then begin Turning Point 1.'
  ][step];}
  function setupContent(step){
    if(step===0) return `<h3>Which mission are you playing?</h3><p>You can review the objective before committing.</p><div class="mission-list">${missions.map(m=>`<button class="mission-choice ${state.missionId===m.id?'selected':''}" data-mission="${m.id}"><small>${m.number}</small><strong>${m.name}</strong><span>${m.brief}</span></button>`).join('')}</div><div class="wizard-actions"><button class="btn ghost" id="setupHome">Back</button><button class="btn primary" id="setupNext" ${state.missionId?'':'disabled'}>Next</button></div>`;
    if(step===1){const m=mission();const checks=['Place walls and hatchways as shown','Place mission objective markers','Identify the Player drop zone','Identify NPO deployment areas'];const allChecked=checks.every((_,i)=>state.setupChecks[i]);return `<h3>${m.name} board setup</h3><p><strong>Objective:</strong> ${m.objective}</p>${boardSvg(m.id)}<div class="setup-bulk-row"><button class="btn secondary" id="checkAllSetup" ${allChecked?'disabled':''}>Check All</button></div><div class="checklist">${checks.map((c,i)=>`<label class="check-row"><input type="checkbox" data-check="${i}" ${state.setupChecks[i]?'checked':''}><span><strong>${c}</strong><small>${i===0?'Use the official mission map shown above to place the terrain and markers.':'Confirm this step on the physical board.'}</small></span></label>`).join('')}</div><div class="wizard-actions"><button class="btn ghost" id="setupBack">Back</button><button class="btn primary" id="setupNext" ${allChecked?'':'disabled'}>Board Ready</button></div>`;}
    if(step===2){const m=mission();return `<h3>Mission starting roster</h3><p>${m.name} begins with <strong>${missionSetup(m)}</strong> NPOs.</p>${state.roster.length?`<div class="summary-box"><strong>${state.roster.length} NPOs generated</strong><br>${rosterBreakdown()}</div><div class="roster-preview">${state.roster.map(n=>operativeCard(n,false)).join('')}</div>`:`<div class="empty">No roster generated yet.</div>`}<div class="wizard-actions"><button class="btn ghost" id="setupBack">Back</button><button class="btn secondary" id="generateBtn">${state.roster.length?'Regenerate':'Generate'} Roster</button><button class="btn primary" id="setupNext" ${state.roster.length||missionSetup(m)==='0'?'':'disabled'}>Continue</button></div>`;}
    if(step===3){const allPlaced=state.roster.every(n=>n.deployed);return `<h3>Deploy the NPOs</h3><p>${missionSetup()==='0'?'This mission starts with no deployed NPOs. The Guide will add them as rooms awaken.':'Place each NPO on the physical board, then mark it deployed.'}</p>${state.roster.length?`<div class="setup-bulk-row"><button class="btn secondary" id="placeAllNpos" ${allPlaced?'disabled':''}>Place All</button></div>`:''}<div class="deployment-list">${state.roster.length?state.roster.map(n=>`<div class="deployment-item ${n.deployed?'done':''}"><span class="deployment-copy"><strong class="deployment-name">${escapeHtml(n.name)}</strong><small class="deployment-type">${escapeHtml(n.behavior)}</small></span><button class="btn ${n.deployed?'ghost':'secondary'} deployment-place-btn" data-deploy="${n.id}">${n.deployed?'Placed':'Mark Placed'}</button></div>`).join(''):'<div class="summary-box"><strong>No starting NPO deployment required.</strong></div>'}</div><div class="wizard-actions"><button class="btn ghost" id="setupBack">Back</button><button class="btn primary" id="setupNext" ${allPlaced?'':'disabled'}>NPOs Deployed</button></div>`;}
    if(step===4){
      const selected=new Set(state.playerRoster||[]);
      const selectedDefs=selectedPlayerOperatives();
      const gravisCount=selectedDefs.filter(o=>o.gravis).length;
      const valid=selected.size===(playerTeamData?.rosterSize||5)&&gravisCount<=1;
      const cards=(playerTeamData?.operatives||[]).map(o=>{
        const chosen=selected.has(o.id);
        const gravisBlocked=!chosen&&o.gravis&&gravisCount>=1;
        return `<button type="button" class="player-roster-card ${chosen?'selected':''}" data-select-player="${o.id}" ${gravisBlocked?'disabled':''}>
          <div class="player-roster-card-head"><div><strong>${escapeHtml(o.name)}</strong><small>${escapeHtml(o.role)}${o.gravis?' · GRAVIS':''}</small></div><span>${chosen?'✓':'+'}</span></div>
          <div class="operative-stat-line"><span><small>APL</small><b>${o.apl}</b></span><span><small>MOVE</small><b>${o.move}"</b></span><span><small>SAVE</small><b>${o.save}+</b></span><span><small>WOUNDS</small><b>${o.wounds}</b></span></div>
        </button>`;
      }).join('');
      return `<h3>Choose your ${escapeHtml(playerTeamData?.teamName||playerTeamEntry()?.name||'Kill Team')} roster</h3><p>Select exactly <strong>${playerTeamData?.rosterSize||5}</strong> unique operatives. Official roster restriction: no more than one <strong>Gravis</strong> operative.</p>
        <div class="player-roster-summary"><strong>${selected.size} / ${playerTeamData?.rosterSize||5} selected</strong><span>${gravisCount} / 1 Gravis</span></div>
        <div class="player-roster-grid">${cards}</div>
        ${selectedDefs.length?`<div class="summary-box"><strong>Selected roster</strong><br>${selectedDefs.map(o=>escapeHtml(o.name)).join(' · ')}</div>`:''}
        <div class="checklist"><label class="check-row"><input id="playerDeployed" type="checkbox" ${state.playerDeployed?'checked':''} ${valid?'':'disabled'}><span><strong>${escapeHtml(playerTeamData?.teamName||playerTeamEntry()?.name||'Player')} operatives deployed</strong><small>Confirm that the selected kill team has been placed in its drop zone.</small></span></label></div>
        <div class="wizard-actions"><button class="btn ghost" id="setupBack">Back</button><button class="btn primary" id="setupNext" ${valid&&state.playerDeployed?'':'disabled'}>Continue</button></div>`;
    }
    return `<h3>Setup complete</h3><div class="summary-box"><strong>${mission().number} · ${mission().name}</strong><br>${state.roster.length} starting NPOs · ${state.playerCount} ${escapeHtml(playerTeamData?.teamName||playerTeamEntry()?.name||'Player')} operatives<br>${selectedPlayerOperatives().map(o=>escapeHtml(o.name)).join(' · ')}</div>${boardSvg(mission().id)}<p><strong>Mission objective:</strong> ${mission().objective}</p><p><strong>Special rule reminder:</strong> ${missionSpecial()}</p><div class="wizard-actions"><button class="btn ghost" id="setupBack">Back</button><button class="btn primary" id="beginGame">Begin Turning Point 1</button></div>`;
  }

  function bindSetup(step){
    $$('.mission-choice').forEach(b=>b.onclick=()=>{state.missionId=b.dataset.mission;state.setupChecks=[];state.roster=[];save();render();});
    $('#setupHome')?.addEventListener('click',()=>{state.screen='home';save();render();});
    $('#setupBack')?.addEventListener('click',()=>{state.setupStep=Math.max(0,state.setupStep-1);save();render();});
    $('#setupNext')?.addEventListener('click',()=>{state.setupStep=Math.min(5,state.setupStep+1);save();render();});
    $$('[data-check]').forEach(c=>c.onchange=()=>{state.setupChecks[Number(c.dataset.check)]=c.checked;save();render();});
    $('#checkAllSetup')?.addEventListener('click',()=>{state.setupChecks=[true,true,true,true];save();render();});
    $('#generateBtn')?.addEventListener('click',()=>{generateRoster();save();render();});
    $$('[data-deploy]').forEach(b=>b.onclick=()=>{const n=state.roster.find(x=>x.id===b.dataset.deploy);n.deployed=!n.deployed;save();render();});
    $('#placeAllNpos')?.addEventListener('click',()=>{state.roster.forEach(n=>n.deployed=true);save();render();});
    $$('[data-select-player]').forEach(button=>button.addEventListener('click',()=>{
      const id=button.dataset.selectPlayer;
      const selected=new Set(state.playerRoster||[]);
      if(selected.has(id))selected.delete(id);
      else if(selected.size<(playerTeamData?.rosterSize||5)){
        const candidate=playerDefinition(id);
        if(candidate?.gravis&&selectedPlayerOperatives().some(o=>o.gravis)){showToast('This Kill Team can include only one Gravis operative.');return;}
        selected.add(id);
      }
      state.playerRoster=[...selected];
      state.playerCount=state.playerRoster.length;
      state.playerReady=state.playerCount;
      state.playerCasualtyIds=[];
      state.playerActivatedIds=[];
      state.playerDeployed=false;
      save();render();
    }));
    $('#playerDeployed')?.addEventListener('change',e=>{state.playerDeployed=e.target.checked;save();render();});
    $('#beginGame')?.addEventListener('click',()=>{
      state.screen='game';
      state.tab='play';
      state.turningPoint=0;
      state.phase='between';
      state.nextSide='player';
      state.playerCount=(state.playerRoster||[]).length;
      state.playerReady=state.playerCount;
      state.roster.forEach(n=>n.ready=false);
      log(`Mission started: ${mission().name}.`);
      startTurningPoint();
    });
  }

  function renderGame(){
    if(state.tab==='play') renderPlay();
    else if(state.tab==='mission') renderMission();
    else if(state.tab==='roster') renderRoster();
    else if(state.tab==='journal') renderJournal();
    else renderHelp();

    if(state.tab!=='play'){
      app.insertAdjacentHTML('afterbegin',`<div class="reference-return"><button class="btn primary" id="returnToGuide">Return to Guided Play</button><small>Reference screens do not change the current Turning Point or activation state.</small></div>`);
      $('#returnToGuide').onclick=()=>{state.tab='play';save();render();};
    }
  }

  function hud(){return `<div class="hud"><div><small>Turning<span class="portrait-break"><br></span> Point</small><strong>${state.turningPoint||'Setup'}</strong></div><button class="hud-cell hud-threat" id="threatHudToggle" type="button" aria-expanded="${threatAdjustOpen}" aria-controls="threatAdjuster"><small>Threat<span class="portrait-break"><br></span> Level</small><strong>${state.threat}</strong></button><div><small>Grade<span class="portrait-break"><br></span> Level</small><strong>${threatGrade()}</strong></div><div><small>Player<span class="portrait-break"><br></span> Ready</small><strong>${state.playerReady}</strong></div><div><small>NPO<span class="portrait-break"><br></span> Ready</small><strong>${readyNpos().length}</strong></div></div><div class="threat-strip ${threatAdjustOpen?'':'hidden'}" id="threatAdjuster"><div><strong>THREAT LEVEL: ${threatLabel()}</strong><small>${threatGrade()===3?'Maximum Grade':`Next Grade at Threat Level ${[1,6,11][threatGrade()]}`}</small></div><div class="threat-meter"><span style="width:${(state.threat/15)*100}%"></span></div><button class="mini-btn" id="threatDown" aria-label="Decrease Threat">−</button><button class="mini-btn" id="threatUp" aria-label="Increase Threat">+</button></div>`;}

  function renderPlay(){
    const nextBanner=state.phase==='firefight'?`<section class="next-activation-banner"><small>NEXT ACTIVATION</small><strong>${state.nextSide==='npo'?'NPO':'Player'}</strong><span>${state.nextSide==='npo'?`${readyNpos().length} ready NPO${readyNpos().length===1?'':'s'}`:`${playerOperativesRemaining()} ready Player operative${playerOperativesRemaining()===1?'':'s'}`}</span></section>`:'';
    const milestone=state.gradeMilestone?`<section class="grade-milestone"><div><small>THREAT ESCALATION</small><strong>Grade ${state.gradeMilestone.grade}: ${escapeHtml(state.gradeMilestone.label)}</strong><span>Threat has reached Level ${state.gradeMilestone.threat}.</span></div><button class="btn ghost compact" id="dismissGradeMilestone">Dismiss</button></section>`:'';
    app.innerHTML=hud()+milestone+`<div class="phase-track"><span class="${state.phase==='strategy'?'current':''}">Strategy</span>›<span class="${state.phase==='firefight'?'current':''}">Activations</span>›<span class="${state.phase==='end'?'current':''}">End Turning Point</span></div>${nextBanner}${nextStepCard()}${state.phase==='firefight'?activationTracker():''}`;
    bindPlay();
  }

  function nextStepCard(){
    if(state.completed) return `<section class="next-card"><span class="phase">MISSION COMPLETE</span><h2>Record the outcome</h2><p>The mission has reached its conclusion. Review the Journal or begin a new game.</p><button class="btn primary big-action" id="newGameFromPlay">Start New Game</button></section>`;
    if(state.phase==='between') return `<section class="next-card"><span class="phase">NEXT STEP</span><h2>Start Turning Point ${state.turningPoint+1}</h2><p>The Guide will ready operatives, determine the current Threat Grade, generate reinforcements, check Tomb World events, and resolve initiative.</p><button class="btn primary big-action" id="startTp">Start Next Turning Point</button></section>`;
    if(state.phase==='strategy') return strategyCard();
    if(state.phase==='end'){
      const npoLosses=Math.max(0,destroyedNpoCount()-(state.tpStartDestroyedNpos||0));
      const playerLosses=Math.max(0,(state.playerCasualtyIds||[]).length-(state.tpStartPlayerCasualties||0));
      const threatChanged=state.threat!==(state.tpStartThreat??state.threat);
      const gradeChanged=threatGrade()!==(state.tpStartGrade??threatGrade());
      return `<section class="next-card"><span class="phase">TURNING POINT ${state.turningPoint} COMPLETE</span><h2>Battle summary</h2><div class="turn-summary-grid"><div><small>Threat</small><strong>${state.tpStartThreat??state.threat} → ${state.threat}</strong><span>${threatChanged?'Changed this Turning Point':'No change'}</span></div><div><small>Grade</small><strong>${state.tpStartGrade??threatGrade()} → ${threatGrade()}</strong><span>${gradeChanged?'Grade increased':'Grade unchanged'}</span></div><div><small>NPOs destroyed</small><strong>${npoLosses}</strong><span>This Turning Point</span></div><div><small>Player casualties</small><strong>${playerLosses}</strong><span>This Turning Point</span></div></div><h3>Score and clean up</h3><p>Score mission objectives, resolve end-of-turn effects, and confirm all temporary markers have been cleared.</p><div class="field"><label>Mission progress: ${missionTracker()}</label><input id="tracker" type="number" min="0" max="${missionTrackerMax()}" value="${state.tracker}"></div><div class="checklist"><label class="check-row"><input id="endChecked" type="checkbox"><span><strong>End-of-turn steps complete</strong><small>Objectives scored, temporary effects resolved, and physical tokens cleaned up.</small></span></label></div><button class="btn primary big-action" id="finishTp" disabled>Finish Turning Point</button></section>`;
    }
    setNextActivation(state.nextSide || state.initiative || 'player');
    if(state.phase==='end'){save();return nextStepCard();}
    if(state.nextSide==='player' && playerOperativesRemaining()>0) return `<section class="next-card"><span class="phase">FIREFIGHT PHASE · ACTIVATION ${state.activationNumber+1}</span><h2>Activate a Player operative</h2><p>Resolve one Player operative on the tabletop. After it completes, the Guide will alternate to an NPO if one is ready.</p><button class="btn primary big-action" id="playerActivation">Resolve Player Activation</button><button class="btn ghost big-action" id="skipPlayer">No Player Operatives Ready</button></section>`;
    if(state.nextSide==='npo' && readyNpos().length>0){const n=nextNpo();return `<section class="next-card"><span class="phase">NPO ACTIVATION · ACTIVATION ${state.activationNumber+1}</span><h2>${escapeHtml(n.name)}</h2><p>${n.type} · ${n.behavior} · ${n.wounds}/${n.maxWounds} wounds</p><div class="summary-box"><strong>Next step:</strong> answer a short set of battlefield questions from this NPO’s perspective. After it completes, the Guide will alternate to a Player operative if one remains.</div><button class="btn primary big-action" id="npoActivation">Guide This NPO</button></section>`;}
    setNextActivation(state.nextSide==='player'?'npo':'player');
    save();
    return nextStepCard();
  }

  let initiativeRolling=false;

  function initiativeDieKind(side){
    const d=state.strategyData||{};
    if(d.playerRoll===d.npoRoll)return 'hit';
    return d.suggestedInitiative===side?'hit':'miss';
  }

  function strategyCard(){
    const d=state.strategyData||{};
    if(state.strategyStage==='summary'){
      const rolls=(d.reinforcements||[]).map(r=>`<div class="reinforcement-result"><div class="dice-row compact">${r.rolls.map(v=>dieHtml({value:v,kind:'hit'})).join('')}</div><strong>${r.type}</strong></div>`).join('');
      return `<section class="next-card"><span class="phase">STRATEGY PHASE · STEP 1 OF 2</span><h2>Complete the Strategy Phase</h2><p class="strategy-intro">Before continuing to initiative, complete the tabletop Strategy Phase for Turning Point ${state.turningPoint}.</p><div class="strategy-phase-guide"><ol><li>Generate Command Points (CP) as required by the game rules.</li><li>Play any Strategic Ploys you want to use this Turning Point.</li><li>Resolve abilities and mission rules that occur during the Strategy Phase.</li><li>Review the Guide's Threat, reinforcement, and Tomb World event results below.</li></ol><p>When all Strategy Phase actions are complete, continue to initiative.</p></div><div class="stat-grid"><div class="stat"><small>THREAT LEVEL</small><strong>${state.threat}</strong></div><div class="stat"><small>GRADE LEVEL</small><strong>${threatGrade()}</strong></div><div class="stat"><small>NPOs Ready</small><strong>${readyNpos().length}</strong></div><div class="stat"><small>Reinforcements</small><strong>${(d.reinforcements||[]).length}</strong></div></div>${rolls?`<h3>Reinforcements generated</h3><div class="reinforcement-grid">${rolls}</div><div class="field"><label>Reinforcement entry point</label><select id="reinforcementEntry"><option>Nearest valid entry point</option><option>Entry Point A</option><option>Entry Point B</option><option>Entry Point C</option><option>Custom placement</option></select></div>`:'<div class="summary-box"><strong>No reinforcements arrive.</strong></div>'}${d.blocked?`<p class="warning-text">${d.blocked} reinforcement(s) were blocked by the 10-NPO battlefield limit.</p>`:''}${d.event?`<div class="summary-box"><strong>${d.event[0]}</strong><br>${d.event[1]}</div>`:'<p>No Tomb World event is required.</p>'}<button class="btn primary big-action" id="continueStrategy">Strategy Phase Complete · Continue to Initiative</button></section>`;
    }
    const auto=state.turningPoint===1;
    return `<section class="next-card"><span class="phase">STRATEGY PHASE · STEP 2 OF 2</span><h2>${auto?`${missionFirstInitiative()==='npo'?'NPOs have':'The Player has'} initiative during Turning Point 1`:'Determine initiative'}</h2>${auto?`<p>During Turning Point 1, ${missionFirstInitiative()==='npo'?'NPOs have':'the Player has'} initiative. Both Player operatives and NPOs begin the Firefight Phase ready.</p>`:`<p>The Guide rolled once for each side. Use the result, reroll both dice, or override it if your tabletop rules require a different outcome.</p><div class="initiative-roll"><div><small>Player</small><div class="dice-row animated-roll" id="playerInitiativeDie">${initiativeRolling?rollingDieHtml():dieHtml({value:state.strategyData.playerRoll,kind:initiativeDieKind('player')})}</div></div><div><small>NPOs</small><div class="dice-row animated-roll" id="npoInitiativeDie">${initiativeRolling?rollingDieHtml():dieHtml({value:state.strategyData.npoRoll,kind:initiativeDieKind('npo')})}</div></div></div><div class="summary-box" id="initiativeResult" ${initiativeRolling?'hidden':''}><strong>${state.strategyData.suggestedInitiative==='npo'?'NPOs win':'The Player wins'} initiative${state.strategyData.playerRoll===state.strategyData.npoRoll?' after the tie-break':''}.</strong></div>`}<div class="quick-actions">${auto?'':`<button class="btn ghost" id="rerollInitiative" ${initiativeRolling?'disabled':''}>Reroll Both</button>`}<button class="btn ${(auto?missionFirstInitiative():d.suggestedInitiative)==='player'?'primary':'secondary'}" data-init="player" ${(auto&&missionFirstInitiative()!=='player')||initiativeRolling?'disabled':''}>Begin Player Activation</button><button class="btn ${(auto?missionFirstInitiative():d.suggestedInitiative)==='npo'?'primary':'secondary'}" data-init="npo" ${(auto&&missionFirstInitiative()!=='npo')||initiativeRolling?'disabled':''}>Begin with NPOs</button></div></section>`;
  }

  function animateInitiativeResult(){
    if(state.turningPoint===1){state.strategyData.suggestedInitiative=missionFirstInitiative();initiativeRolling=false;return;}
    setTimeout(()=>{
      const player=$('#playerInitiativeDie');
      if(player){
        player.innerHTML=dieHtml({value:state.strategyData.playerRoll,kind:initiativeDieKind('player')});
        player.classList.add('settled');
      }
      const npo=$('#npoInitiativeDie');
      if(npo){
        npo.innerHTML=dieHtml({value:state.strategyData.npoRoll,kind:initiativeDieKind('npo')});
        npo.classList.add('settled');
      }
      const result=$('#initiativeResult');
      if(result)result.hidden=false;
      initiativeRolling=false;
      $('#rerollInitiative')?.removeAttribute('disabled');
      $$('[data-init]').forEach(button=>button.removeAttribute('disabled'));
    },700);
  }

  function activationTracker(){
    const activatedIds=new Set(state.playerActivatedIds||[]);
    const casualtyIds=new Set(state.playerCasualtyIds||[]);
    const playerRows=(state.playerRoster||[]).map(operativeId=>{
      const operative=playerDefinition(operativeId);
      const casualty=casualtyIds.has(operativeId);
      const activated=activatedIds.has(operativeId);
      const status=casualty?'ELIMINATED':activated?'ACTIVATED':'READY';
      const cls=casualty?'eliminated':activated?'activated':'ready';
      return `<button type="button" class="tracker-operative player ${cls}" data-player-operative="${operativeId}" title="Select ${escapeHtml(operative?.name||operativeId)} to mark it eliminated or restore it">
        <span>${escapeHtml(operative?.name||operativeId)}</span><strong>${status}</strong>
      </button>`;
    }).join('');
    const npoRows=activeNpos().map(n=>`<div class="tracker-operative npo ${n.ready?'ready':'activated'}"><span>${escapeHtml(n.name)}</span><strong>${n.ready?'READY':'ACTIVATED'}</strong></div>`).join('');
    return `<section class="card activation-tracker">
      <div class="panel-title"><div><p class="eyebrow">ACTIVATION TRACKER</p><h3>${state.activationNumber} activations completed</h3></div><div class="turn-badge">Next: ${state.nextSide==='npo'?'NPO':'Player'}</div></div>
      <div class="tracker-section">
        <small>${escapeHtml(playerTeamData?.teamName||playerTeamEntry()?.name||'Player')} operatives</small>
        <p class="muted compact-copy">Select an operative to mark it eliminated or restore it.</p>
        <div class="tracker-operative-grid">${playerRows||'<span class="muted">No player operatives selected</span>'}</div>
      </div>
      <div class="tracker-section">
        <small>NPOs</small>
        <div class="tracker-operative-grid">${npoRows||'<span class="muted">No active NPOs</span>'}</div>
      </div>
    </section>`;
  }

  function showPlayerOperativeStatus(operativeId){
    const casualties=new Set(state.playerCasualtyIds||[]);
    const eliminated=casualties.has(operativeId);
    const operativeName=playerName(operativeId);
    showModal(operativeName,`
      <p>This status carries across Turning Points and is reflected in the activation tracker and Player Ready count.</p>
      <div class="summary-box"><strong>Current status:</strong> ${eliminated?'Eliminated':'Active'}</div>
      <div class="wizard-actions"><button class="btn ghost" data-close>Cancel</button><button class="btn ${eliminated?'secondary':'danger'}" id="togglePlayerCasualty">${eliminated?'Restore Operative':'Mark Eliminated'}</button></div>`);
    $('#togglePlayerCasualty').onclick=()=>{
      const ids=new Set(state.playerCasualtyIds||[]);
      if(ids.has(operativeId)){
        ids.delete(operativeId);
        log(`${operativeName} restored.`);
      }else{
        ids.add(operativeId);
        if(!state.playerActivatedIds.includes(operativeId))state.playerActivatedIds.push(operativeId);
        log(`${operativeName} eliminated.`);
      }
      state.playerCasualtyIds=[...ids];
      state.playerReady=playerOperativesRemaining();
      setNextActivation(state.nextSide||'npo');
      closeModal();
      save();
      render();
    };
  }

  function bindPlay(){
    $('#dismissGradeMilestone')?.addEventListener('click',()=>{state.gradeMilestone=null;save();render();});
    $$('[data-player-operative]').forEach(button=>button.addEventListener('click',()=>showPlayerOperativeStatus(button.dataset.playerOperative)));
    $('#startTp')?.addEventListener('click',startTurningPoint);
    $('#continueStrategy')?.addEventListener('click',()=>{state.reinforcementEntry=$('#reinforcementEntry')?.value||state.reinforcementEntry;state.strategyStage='initiative';initiativeRolling=state.turningPoint!==1;save();render();if(initiativeRolling)animateInitiativeResult();});
    $('#rerollInitiative')?.addEventListener('click',()=>{rollInitiative();initiativeRolling=true;save();render();animateInitiativeResult();});
    $$('[data-init]').forEach(b=>b.onclick=()=>beginFirefight(b.dataset.init));
    $('#playerActivation')?.addEventListener('click',()=>showPlayerActivation());
    $('#skipPlayer')?.addEventListener('click',()=>{state.playerReady=0;setNextActivation('npo');log('No Player operatives remain ready.');save();render();});
    $('#npoActivation')?.addEventListener('click',showNpoWizard);
    $('#tracker')?.addEventListener('change',e=>{state.tracker=Math.max(0,Math.min(missionTrackerMax(),Number(e.target.value)||0));save();});
    $('#endChecked')?.addEventListener('change',e=>{$('#finishTp').disabled=!e.target.checked;});
    $('#finishTp')?.addEventListener('click',()=>{state.phase='between';state.strategyStage=null;state.strategyData=null;state.newIds=[];log(`Turning Point ${state.turningPoint} completed.`);save();render();});
    $('#newGameFromPlay')?.addEventListener('click',confirmNewGame);
    $('#threatHudToggle')?.addEventListener('click',()=>{threatAdjustOpen=!threatAdjustOpen;render();});
    $('#threatUp')?.addEventListener('click',()=>{setThreat(1,'Manual adjustment');save();render();});
    $('#threatDown')?.addEventListener('click',()=>{setThreat(-1,'Manual adjustment');save();render();});
  }

  function startTurningPoint(){
    state.turningPoint++;
    state.tpStartThreat=state.threat;
    state.tpStartGrade=threatGrade();
    state.tpStartDestroyedNpos=destroyedNpoCount();
    state.tpStartPlayerCasualties=(state.playerCasualtyIds||[]).length;
    state.gradeMilestone=null;
    state.playerReady=Math.max(0,state.playerCount-(state.playerCasualtyIds||[]).length);
    state.playerActivated=0;state.npoActivated=0;state.activationNumber=0;state.activationHistory=[];state.playerActivatedIds=[];
    const grade=threatGrade();
    activeNpos().forEach(n=>n.ready=true);
    const reinforcements=[];
    let blocked=0;
    if(state.turningPoint>1 && grade>0){
      const requested=grade, slots=Math.max(0,MAX_NPOS-activeNpos().length), amount=Math.min(requested,slots); blocked=requested-amount;
      for(let i=0;i<amount;i++){
        const rr=randomReinforcement();const type=rr.type,p=profiles[type];
        const n={id:uid(),name:`${type} R${state.turningPoint}-${i+1}`,type,behavior:p.behavior,maxWounds:p.wounds,wounds:p.wounds,save:p.save,attack:{...p.attack},ready:true,deployed:true};
        state.roster.push(n);state.newIds.push(n.id);reinforcements.push(rr);
      }
    }
    let event=null;
    if(grade===3){event=events[roll(events.length)-1];applyStrategyEvent(event);}
    state.strategyData={grade,reinforcements,blocked,event,playerRoll:null,npoRoll:null,suggestedInitiative:'player'};
    rollInitiative();
    state.phase='strategy';state.strategyStage='summary';state.nextSide='player';state.activeNpoId=null;
    log(`Turning Point ${state.turningPoint} started. Grade ${grade}; ${reinforcements.length} reinforcement(s).`);
    save();render();
  }

  function rollInitiative(){
    if(!state.strategyData)state.strategyData={};
    if(state.turningPoint===1){
      state.strategyData.playerRoll=null;
      state.strategyData.npoRoll=null;
      state.strategyData.suggestedInitiative='player';
      return;
    }
    const p=roll(),n=roll();
    state.strategyData.playerRoll=p;
    state.strategyData.npoRoll=n;
    state.strategyData.suggestedInitiative=n>p?'npo':'player';
  }

  function beginFirefight(side){
    state.initiative=side;
    state.phase='firefight';
    state.strategyStage=null;
    setNextActivation(side);
    log(`${side==='npo'?'NPOs':'Player'} begin the Firefight Phase with initiative.`);
    save();
    render();
  }

  function applyStrategyEvent(event){
    if(!event)return;
    if(event[0]==='Stirrings of Horror')setThreat(1,event[0]);
    if(event[0]==='Living Metal Flux')activeNpos().forEach(n=>{if(n.wounds<n.maxWounds)n.wounds=Math.min(n.maxWounds,n.wounds+rollD3()+2);});
    if(event[0]==='Awakened Warrior' && activeNpos().length<MAX_NPOS){const p=profiles['Necron Warrior'];state.roster.push({id:uid(),name:`Necron Warrior E${state.turningPoint}`,type:'Necron Warrior',behavior:p.behavior,maxWounds:p.wounds,wounds:p.wounds,save:p.save,attack:{...p.attack},ready:true,deployed:true});}
  }

  function randomReinforcement(){ const a=roll(),b=roll(),r=a+b; return {rolls:[a,b],total:r,type:r<=4?'Canoptek Scarab Swarm':r<=6?'Canoptek Macrocyte':r<=10?'Necron Warrior':'Canoptek Tomb Crawler'}; }
  function nextNpo(){ let n=state.roster.find(x=>x.id===state.activeNpoId&&x.ready&&x.wounds>0); if(!n){n=readyNpos().sort((a,b)=>priority(b)-priority(a))[0];state.activeNpoId=n?.id||null;} return n; }
  function priority(n){return ({Guardian:4,Marksman:3,Brawler:2,Sentinel:1}[n.behavior]||1)+(n.wounds/n.maxWounds<.5?-.5:0);}

  function remainingPlayerOperatives(){
    const used=new Set(state.playerActivatedIds||[]);
    const casualties=new Set(state.playerCasualtyIds||[]);
    return (state.playerRoster||[]).filter(id=>!used.has(id)&&!casualties.has(id));
  }

  
  const PLAYER_ACTION_COSTS={
    move:1,
    dash:1,
    charge:1,
    fallBack:2,
    shoot:1,
    melee:1,
    damage:1,
    hatch:1,
    breach:1,
    objective:1,
    pass:0
  };

  function playerActionCost(stage){
    return Object.entries(PLAYER_ACTION_COSTS).reduce((total,[key,cost])=>total+(stage[key]?cost:0),0);
  }

  function playerActionConflicts(stage){
    const conflicts=[];
    if(stage.charge && (stage.move || stage.dash || stage.fallBack)){
      conflicts.push('Charge cannot be combined with Move, Dash, or Fall Back.');
    }
    if(stage.fallBack && (stage.move || stage.charge)){
      conflicts.push('Fall Back cannot be combined with Move or Charge.');
    }
    if(stage.pass && playerActionCost({...stage,pass:false})>0){
      conflicts.push('Pass cannot be combined with another action.');
    }
    return conflicts;
  }

function showPlayerActivation(stage={}){
    const remaining=remainingPlayerOperatives();
    if(!remaining.length){
      state.playerReady=0;
      setNextActivation('npo');
      save();
      render();
      return;
    }

    const checked=key=>stage[key]?'checked':'';
    const selectedId=String(stage.playerOperativeId||'');
    const shootPending=stage.pendingShoot||null;
    const meleePending=stage.pendingMelee||null;

    showModal('Resolve Player Activation',`
      <p>Choose the Player operative being activated. That operative cannot activate again during this Turning Point after the activation is confirmed.</p>
      <div class="field">
        <label>Player operative</label>
        <select id="playerOperativeSelect">
          <option value="">Select a Player operative...</option>
          ${remaining.map(id=>`<option value="${id}" ${selectedId===id?'selected':''}>${escapeHtml(playerName(id))}</option>`).join('')}
        </select>
      </div>
      <fieldset id="playerActivationControls" ${selectedId?'':'disabled'}>
        <div class="activation-apl-bar">
          <div class="field apl-field">
            <label>APL</label>
            <select id="playerApl">
              ${[1,2,3,4,5].map(v=>`<option value="${v}" ${Number(stage.apl||playerDefinition(selectedId)?.apl||3)===v?'selected':''}>${v}</option>`).join('')}
            </select>
          </div>
          <div class="ap-usage" id="apUsage"><small>AP used</small><strong>0 / ${Number(stage.apl||3)}</strong></div>
        </div>
        <div id="apWarning" class="warning-text hidden"></div>
        <p class="muted">Select everything this operative will do. Shooting and Melee attacks are resolved only after you press Complete Activation.</p>
        <div class="activation-groups">
          <section class="activation-group">
            <div class="activation-group-title"><span>↔</span><div><strong>Movement</strong><small>Position and control actions</small></div></div>
            <div class="toggle-list player-action-list">
              <label><input type="checkbox" id="eaMove" ${checked('move')}><span>Move <small>1 AP</small></span></label>
              <label><input type="checkbox" id="eaDash" ${checked('dash')}><span>Dash <small>1 AP</small></span></label>
              <label><input type="checkbox" id="eaCharge" ${checked('charge')}><span>Charge <small>1 AP</small></span></label>
              <label><input type="checkbox" id="eaFallBack" ${checked('fallBack')}><span>Fall Back <small>2 AP</small></span></label>
            </div>
          </section>

          <section class="activation-group">
            <div class="activation-group-title"><span>⚔</span><div><strong>Combat</strong><small>Resolved after Complete Activation</small></div></div>
            <div class="combat-action-card">
              <label><input type="checkbox" id="eaShoot" ${checked('shoot')}><span><strong>Shoot</strong><small>1 AP · One Shooting action for this operative</small></span></label>
              ${shootPending?`<div class="pending-attack-summary"><strong>Pending:</strong> ${escapeHtml(shootPending.targetName)} · ${shootPending.damage} damage</div>`:''}
            </div>
            <div class="combat-action-card">
              <label><input type="checkbox" id="eaMelee" ${checked('melee')||checked('fight')}><span><strong>Melee</strong><small>1 AP · One Melee action for this operative</small></span></label>
              ${meleePending?`<div class="pending-attack-summary"><strong>Pending:</strong> ${escapeHtml(meleePending.targetName)} · ${meleePending.damage} damage</div>`:''}
            </div>
            <div class="toggle-list player-action-list compact-actions">
              <label><input type="checkbox" id="eaDamage" ${checked('damage')}><span>Damaged an NPO with another action <small>1 AP</small></span></label>
            </div>
          </section>

          <section class="activation-group">
            <div class="activation-group-title"><span>▣</span><div><strong>Battlefield</strong><small>Terrain and mission interactions</small></div></div>
            <div class="toggle-list player-action-list">
              <label><input type="checkbox" id="eaHatch" ${checked('hatch')}><span>Operate Hatch <small>1 AP</small></span></label>
              <label><input type="checkbox" id="eaBreach" ${checked('breach')}><span>Breach <small>1 AP</small></span></label>
              <label><input type="checkbox" id="eaObjective" ${checked('objective')}><span>Mission or objective action <small>1 AP</small></span></label>
            </div>
          </section>

          <section class="activation-group pass-group">
            <div class="toggle-list player-action-list">
              <label><input type="checkbox" id="eaPass" ${checked('pass')}>Pass / no action recorded</label>
            </div>
          </section>
        </div>
        <div class="wizard-actions"><button class="btn ghost" id="cancelPlayerActivation">Cancel</button><button class="btn primary" id="confirmPlayer">Complete Activation</button></div>
      </fieldset>`);

    const operativeSelect=$('#playerOperativeSelect');
    const controls=$('#playerActivationControls');
    operativeSelect.addEventListener('change',()=>{
      const selectedOperative=playerDefinition(operativeSelect.value);const updated={...stage,playerOperativeId:operativeSelect.value||'',apl:Number(selectedOperative?.apl||$('#playerApl')?.value||stage.apl||3)};
      showPlayerActivation(updated);
    });

    const actionIds=['eaMove','eaDash','eaCharge','eaFallBack','eaShoot','eaMelee','eaDamage','eaHatch','eaBreach','eaObjective'];
    const clearPass=()=>{if($('#eaPass'))$('#eaPass').checked=false;};

    function updatePlayerActionAvailability(){
      const current=readPlayerActivationStage(stage);
      const apl=Number($('#playerApl')?.value||current.apl||3);
      current.apl=apl;
      const used=playerActionCost(current);
      const conflicts=playerActionConflicts(current);
      const usage=$('#apUsage');
      if(usage)usage.innerHTML=`<small>AP used</small><strong>${used} / ${apl}</strong>`;
      const warning=$('#apWarning');
      const messages=[...conflicts];
      if(used>apl)messages.push(`This activation uses ${used} AP, but the operative only has ${apl} APL.`);
      if(warning){
        warning.textContent=messages.join(' ');
        warning.classList.toggle('hidden',messages.length===0);
      }
      $('#confirmPlayer').disabled=used>apl || conflicts.length>0;

      // Disable unchecked actions that would exceed APL if added.
      const map={
        eaMove:'move',eaDash:'dash',eaCharge:'charge',eaFallBack:'fallBack',
        eaShoot:'shoot',eaMelee:'melee',eaDamage:'damage',eaHatch:'hatch',
        eaBreach:'breach',eaObjective:'objective'
      };
      Object.entries(map).forEach(([id,key])=>{
        const box=$(`#${id}`);
        if(!box)return;
        if(box.checked){box.disabled=false;return;}
        const hypothetical={...current,[key]:true};
        box.disabled=playerActionCost(hypothetical)>apl || playerActionConflicts(hypothetical).length>0;
      });
    }

    $('#eaPass')?.addEventListener('change',e=>{
      if(e.target.checked)actionIds.forEach(id=>{const box=$(`#${id}`);if(box)box.checked=false;});
      updatePlayerActionAvailability();
    });
    actionIds.forEach(id=>$(`#${id}`)?.addEventListener('change',e=>{
      if(e.target.checked)clearPass();
      updatePlayerActionAvailability();
    }));
    $('#playerApl')?.addEventListener('change',updatePlayerActionAvailability);
    updatePlayerActionAvailability();

    $('#cancelPlayerActivation').onclick=()=>{closeModal();render();};
    $('#confirmPlayer').onclick=()=>{
      const finalStage=readPlayerActivationStage(stage);
      const used=playerActionCost(finalStage);
      const conflicts=playerActionConflicts(finalStage);
      if(used>finalStage.apl || conflicts.length){
        showToast(conflicts[0] || `This operative is limited to ${finalStage.apl} AP.`);
        return;
      }
      if(!finalStage.playerOperativeId){
        showToast('Select a Player operative first.');
        return;
      }
      if(!playerActivationHasAction(finalStage)){
        showModal('No actions selected',`<p>Mark ${escapeHtml(playerName(finalStage.playerOperativeId))} as activated without recording an action?</p><div class="wizard-actions"><button class="btn ghost" id="returnPlayerActivation">Go Back</button><button class="btn primary" id="confirmEmptyPlayerActivation">Continue</button></div>`);
        $('#returnPlayerActivation').onclick=()=>showPlayerActivation(finalStage);
        $('#confirmEmptyPlayerActivation').onclick=()=>resolvePendingPlayerAttacks(finalStage);
        return;
      }
      resolvePendingPlayerAttacks(finalStage);
    };
  }

  function readPlayerActivationStage(previous={}){
    const shoot=Boolean($('#eaShoot')?.checked);
    const melee=Boolean($('#eaMelee')?.checked);
    return {
      playerOperativeId:String($('#playerOperativeSelect')?.value||previous.playerOperativeId||''),
      apl:Number($('#playerApl')?.value||previous.apl||3),
      move:Boolean($('#eaMove')?.checked),
      dash:Boolean($('#eaDash')?.checked),
      charge:Boolean($('#eaCharge')?.checked),
      fallBack:Boolean($('#eaFallBack')?.checked),
      shoot,
      melee,
      damage:Boolean($('#eaDamage')?.checked),
      hatch:Boolean($('#eaHatch')?.checked),
      breach:Boolean($('#eaBreach')?.checked),
      objective:Boolean($('#eaObjective')?.checked),
      pass:Boolean($('#eaPass')?.checked),
      pendingShoot:shoot?previous.pendingShoot||null:null,
      pendingMelee:melee?previous.pendingMelee||null:null
    };
  }

  function playerActivationHasAction(stage){
    return Boolean(stage.move || stage.dash || stage.charge || stage.fallBack || stage.shoot || stage.melee ||
      stage.damage || stage.hatch || stage.breach || stage.objective || stage.pass);
  }

  function playerActivationSummary(stage){
    const actions=[];
    if(stage.move)actions.push('Move');
    if(stage.dash)actions.push('Dash');
    if(stage.charge)actions.push('Charge');
    if(stage.fallBack)actions.push('Fall Back');
    if(stage.shoot)actions.push('Shooting attack resolved');
    if(stage.melee)actions.push('Melee attack resolved');
    if(stage.damage)actions.push('Damaging action');
    if(stage.hatch)actions.push('Operate Hatch');
    if(stage.breach)actions.push('Breach');
    if(stage.objective)actions.push('Mission action');
    if(stage.pass)actions.push('Pass / no action recorded');
    return actions.length?actions.join(', '):'No actions recorded';
  }

  function projectedNpoWounds(npoId,stage){
    let wounds=state.roster.find(n=>n.id===npoId)?.wounds||0;
    for(const pending of [stage.pendingShoot,stage.pendingMelee]){
      if(pending?.targetId===npoId)wounds=pending.after;
    }
    return wounds;
  }

  function resolvePendingPlayerAttacks(stage){
    if(stage.shoot&&!stage.pendingShoot){
      showPendingPlayerAttackWizard(stage,'shoot',result=>resolvePendingPlayerAttacks({...stage,pendingShoot:result}),()=>showPlayerActivation(stage));
      return;
    }
    if(stage.melee&&!stage.pendingMelee){
      showPendingPlayerAttackWizard(stage,'melee',result=>resolvePendingPlayerAttacks({...stage,pendingMelee:result}),()=>showPlayerActivation(stage));
      return;
    }
    showPlayerActivationConfirmation(stage);
  }

  function showPlayerActivationConfirmation(stage){
    const pending=[stage.pendingShoot,stage.pendingMelee].filter(Boolean);
    const attackRows=pending.map(p=>`<div class="summary-box"><strong>${p.attackType==='shoot'?'Shooting':'Melee'}:</strong> ${escapeHtml(p.targetName)} · ${p.before} → ${p.after} wounds (${p.damage} damage)</div>`).join('');
    showModal('Confirm Player Activation',`
      <p>${escapeHtml(playerName(stage.playerOperativeId))} will be marked activated. NPO damage has not been applied yet.</p>
      <div class="summary-box"><strong>AP used:</strong> ${playerActionCost(stage)} / ${stage.apl}</div>
      ${attackRows||'<div class="summary-box"><strong>No attacks to apply.</strong></div>'}
      <div class="summary-box"><strong>Actions:</strong> ${escapeHtml(playerActivationSummary(stage))}</div>
      <div class="wizard-actions"><button class="btn ghost" id="backToPlayerActivation">Go Back</button><button class="btn primary" id="commitPlayerActivation">Confirm Activation</button></div>`);
    $('#backToPlayerActivation').onclick=()=>showPlayerActivation(stage);
    $('#commitPlayerActivation').onclick=()=>{
      applyPendingPlayerDamage(stage);
      completePlayerActivation(stage);
    };
  }

  function applyPendingPlayerDamage(stage){
    for(const pending of [stage.pendingShoot,stage.pendingMelee]){
      if(!pending)continue;
      const n=state.roster.find(x=>x.id===pending.targetId);
      if(!n)continue;
      const before=n.wounds;
      n.wounds=Math.max(0,pending.after);
      if(n.wounds===0)n.ready=false;
      log(`${playerName(stage.playerOperativeId)} ${pending.attackType==='shoot'?'shot':'made a Melee attack against'} ${n.name} for ${pending.damage} damage (${before} → ${n.wounds} wounds).`);
    }
  }

  function completePlayerActivation(stage={}){
    let inc=0;
    if(stage.shoot)inc++;
    if(stage.melee)inc++;
    if(stage.damage)inc++;
    if(stage.hatch){
      const r=roll();
      if(r>=4)inc++;
      showToast(`Operate Hatch rolled ${r}${r>=4?'... Threat +1':'... no Threat increase'}`);
    }
    if(stage.breach){
      inc++;
      const r=roll();
      if(r>=4)inc++;
      showToast(`Breach rolled ${r}${r>=4?'... Threat +2 total':'... Threat +1 total'}`);
    }
    if(inc)setThreat(inc,'Player activation');
    const operativeId=String(stage.playerOperativeId);
    if(!state.playerActivatedIds.includes(operativeId))state.playerActivatedIds.push(operativeId);
    state.playerReady=playerOperativesRemaining();
    state.playerActivated=state.playerActivatedIds.length;
    state.activationNumber++;
    const summary=playerActivationSummary(stage);
    state.activationHistory.unshift({side:'player',label:playerName(operativeId),summary});
    advanceAfterActivation('player');
    log(`${playerName(operativeId)} completed activation: ${summary}.`);
    closeModal();
    save();
    render();
  }

  function showPendingPlayerAttackWizard(stage,attackType,onResolved,onCancel){
    const targets=activeNpos().filter(n=>projectedNpoWounds(n.id,stage)>0);
    if(!targets.length){
      showToast('No active NPO is available as a target.');
      showPlayerActivation(stage);
      return;
    }
    const attackLabel=attackType==='shoot'?'Shooting':'Melee';
    showModal(`Resolve ${attackLabel} Attack`,`
      <p>Select the target NPO. This attack remains pending until the entire Player activation is confirmed.</p>
      <div class="field"><label>Target NPO</label><select id="combatTarget"><option value="">Select a target NPO...</option>${targets.map(n=>`<option value="${n.id}">${escapeHtml(n.name)} · ${projectedNpoWounds(n.id,stage)}/${n.maxWounds} projected wounds · Save ${n.save}+</option>`).join('')}</select></div>
      <fieldset id="combatControls" class="combat-fieldset" disabled>
        <div class="combat-grid">
          ${spinnerField('playerAttackDice','Attack dice',4,1,12)}
          ${spinnerField('playerHit','Hit on',3,2,6)}
          ${spinnerField('playerNormalDamage','Normal damage',3,0,12)}
          ${spinnerField('playerCritDamage','Critical damage',4,0,15)}
          ${spinnerField('playerAp','AP',0,0,3)}
          ${spinnerField('npoDefenseDice','NPO Defense Dice',3,0,6)}
        </div>
        <label class="check-row compact-check"><input type="checkbox" id="npoCover"><span><strong>NPO retains one normal save for cover</strong></span></label>
        <div id="combatResults" class="combat-results"><p>Select a target NPO to begin.</p></div>
        <div class="wizard-actions"><button class="btn ghost" id="cancelPendingAttack">Cancel</button><button class="btn primary" id="rollPendingAttack">Roll Attack & Saves</button></div>
      </fieldset>`);
    bindSpinners(modal);
    const targetSelect=$('#combatTarget');
    const controls=$('#combatControls');
    targetSelect.addEventListener('change',()=>{
      controls.disabled=!targetSelect.value;
      if(targetSelect.value)$('#combatResults').innerHTML='<p>Set the profile, then roll the attack.</p>';
    });
    $('#cancelPendingAttack').onclick=onCancel;
    $('#rollPendingAttack').onclick=()=>previewPendingPlayerAttack(stage,attackType,onResolved,onCancel);
  }

  function previewPendingPlayerAttack(stage,attackType,onResolved,onCancel){
    const n=state.roster.find(x=>x.id===$('#combatTarget').value);
    if(!n)return;
    const profile={dice:num('playerAttackDice'),hit:num('playerHit'),normal:num('playerNormalDamage'),crit:num('playerCritDamage')};
    const attackDice=rollAttack(profile);
    const defense=resolveDefense(attackDice,num('npoDefenseDice'),n.save,num('playerAp'),$('#npoCover').checked,profile);
    const before=projectedNpoWounds(n.id,stage);
    const after=Math.max(0,before-defense.damage);
    const result={attackType,targetId:n.id,targetName:n.name,before,after,damage:defense.damage};

    $('#combatResults').innerHTML=`<div class="combat-stage"><small>PLAYER ATTACK DICE</small><div class="dice-row animated-roll" id="playerAttackDiceResult">${attackDice.map(()=>rollingDieHtml()).join('')}</div></div>
      <div class="combat-stage"><small>NPO SAVE DICE</small><div class="dice-row animated-roll" id="npoSaveDiceResult">${defense.saveDice.map(()=>rollingDieHtml()).join('')||'<span class="muted">No save dice rolled</span>'}</div>${defense.coverRetained?'<span class="cover-retain">+ 1 retained normal cover save</span>':''}</div>
      <div class="damage-summary"><div><small>Unsaved normal hits</small><strong>${defense.normalRemaining}</strong></div><div><small>Unsaved critical hits</small><strong>${defense.critRemaining}</strong></div><div><small>Pending damage</small><strong>${defense.damage}</strong></div><div><small>Projected wounds</small><strong>${before} → ${after}</strong></div></div>
      <p class="muted">No wounds have been changed. Use This Result stores the attack until the Player activation is confirmed.</p>`;

    const button=$('#rollPendingAttack');
    button.textContent='Use This Result';
    button.onclick=()=>onResolved(result);
    $('#cancelPendingAttack').onclick=onCancel;

    setTimeout(()=>{
      const a=$('#playerAttackDiceResult');if(a){a.innerHTML=attackDice.map(dieHtml).join('');a.classList.add('settled');}
      const d=$('#npoSaveDiceResult');if(d&&defense.saveDice.length){d.innerHTML=defense.saveDice.map(dieHtml).join('');d.classList.add('settled');}
    },700);
  }

  const npoQuestions = [
    {key:'engaged',title:'Is a Player operative in control range?',help:'Choose Yes when this NPO can immediately Fight a Player operative without moving.'},
    {key:'charge',title:'Can this NPO complete a Charge?',help:'Choose Yes only when a legal Charge can finish within control range of a Player operative.'},
    {key:'shot',title:'Does this NPO have a valid shooting target?',help:'The target must be valid for the NPO’s ranged weapon after any movement you expect it to make.'},
    {key:'objective',title:'Is a Player operative controlling a mission objective?',help:'This gives mission denial priority over an otherwise equal target.'},
    {key:'wounded',title:'Is a valid Player target wounded?',help:'A wounded target is below its starting wounds and can reasonably be attacked by this NPO.'},
    {key:'hatch',title:'Does a closed hatch block the best route?',help:'Choose Yes when operating the hatch is the clearest way to advance toward a Player or objective.'},
    {key:'cover',title:'Can the NPO remain in cover while acting?',help:'This affects whether the Guide recommends holding position, moving minimally, or advancing aggressively.'},
    {key:'clustered',title:'Are multiple valid Player targets clustered together?',help:'This is used as a final target-priority tie breaker for pressure and board control.'}
  ];

  function showNpoWizard(){
    const n=nextNpo(); if(!n)return;
    runNpoPrompt(n,0,{});
  }

  function runNpoPrompt(n,index,answers){
    const q=npoQuestions[index];
    const progress=Math.round((index/npoQuestions.length)*100);
    showModal(`Guide ${escapeHtml(n.name)}`,`<div class="ai-wizard">
      <div class="ai-progress-head"><span>QUESTION ${index+1} OF ${npoQuestions.length}</span><strong>${progress}%</strong></div>
      <div class="ai-progress"><span style="width:${progress}%"></span></div>
      <p class="eyebrow">NPO PERSPECTIVE</p>
      <h3>${q.title}</h3>
      <p>${q.help}</p>
      <div class="ai-choice-grid">
        <button class="ai-choice yes" data-answer="yes"><span>✓</span><strong>Yes</strong></button>
        <button class="ai-choice no" data-answer="no"><span>×</span><strong>No</strong></button>
      </div>
      <div class="wizard-actions">
        <button class="btn ghost" data-close>Cancel</button>
        <button class="btn ghost" id="aiBack" ${index===0?'disabled':''}>Back</button>
      </div>
    </div>`);
    $$('[data-answer]',modal).forEach(btn=>btn.onclick=()=>{
      const next={...answers,[q.key]:btn.dataset.answer==='yes'};
      if(index<npoQuestions.length-1) runNpoPrompt(n,index+1,next);
      else resolveNpo(n,next);
    });
    $('#aiBack')?.addEventListener('click',()=>runNpoPrompt(n,index-1,answers));
  }

  function chooseNpoDecision(n,c){
    const path=[];
    let action,target='closest valid Player operative',stance='Engage',threat=0,reason='Advance pressure toward the nearest relevant target.';
    if(c.objective){target='Player operative controlling the mission objective';path.push('Mission objective is threatened');}
    else if(c.wounded){target='wounded valid Player operative';path.push('A wounded target can be finished');}
    else if(c.clustered){target='the Player target in the largest cluster';path.push('Clustered targets offer the most board pressure');}
    else path.push('Use the closest valid Player operative');

    if(c.engaged){
      action='Fight the selected target, then reposition toward cover or the mission objective';
      reason='A Player is already in control range, so immediate melee takes priority.';threat=1;path.unshift('Player in control range → Fight');
    } else if(c.charge && (n.behavior==='Brawler'||n.behavior==='Guardian'||c.objective||c.wounded)){
      action='Charge the selected target, then Fight';
      reason=`${n.behavior} behavior favors decisive melee when the target is tactically important.`;threat=1;path.unshift('Legal high-value Charge → Charge and Fight');
    } else if(c.shot){
      const movement=c.cover?'Remain in cover or move only enough to gain line of sight':'Move to the nearest legal firing position';
      action=`${movement}, then Shoot the selected target`;
      reason='A valid ranged attack is available and no higher-priority melee action applies.';threat=1;path.unshift('Valid shooting target → Shoot');
    } else if(c.hatch){
      action='Operate the blocking hatch, then move toward the selected target';
      reason='The closed hatch prevents the best advance and no immediate attack is available.';path.unshift('Route blocked by hatch → Operate Hatch');
    } else if(c.objective){
      action='Move toward and contest the mission objective, retaining cover where possible';
      reason='No attack is available, so denying mission progress becomes the priority.';path.unshift('No attack → Contest objective');
    } else {
      action='Move toward the selected target, retaining cover and avoiding unnecessary exposure';
      reason='No immediate attack or mission interaction is available.';path.unshift('No attack available → Reposition');
      stance=c.cover?'Conceal':'Engage';
    }
    return {action,target,stance,threat,reason,path};
  }

  function resolveNpo(n,c){
    state.npoAttackTargetId=null;
    const decision=chooseNpoDecision(n,c);
    const attacks=decision.action.includes('Fight')||decision.action.includes('Shoot');
    const dice=[];
    if(decision.threat)setThreat(decision.threat,`${n.name} ${decision.action.includes('Fight')?'Fight':'Shoot'}`);
    n.ready=false;state.npoActivated++;state.activationNumber++;
    state.activationHistory.unshift({side:'npo',label:n.name,action:decision.action,target:null});
    state.activeNpoId=null;advanceAfterActivation('npo');
    state.lastActivation={name:n.name,...decision,dice,answers:c,attackRequired:attacks,targetConfirmed:false};
    log(`${n.name}: ${decision.action}.`);save();

    renderNpoDecisionResult(n,decision,dice,c,false,false,attacks,false);
  }

  function initiativeSummary(dice){
    const crits=dice.filter(d=>d.kind==='crit').length;
    const hits=dice.filter(d=>d.kind==='hit').length;
    const misses=dice.filter(d=>d.kind==='miss').length;
    if(crits===0&&hits===0)return 'Attack missed. No saves or damage required.';
    return `${crits} critical · ${hits} normal · ${misses} miss`;
  }

  function renderNpoDecisionResult(n,decision,dice,answers,attackResolved,animateDice=true,attackRequired=(decision.action.includes('Fight')||decision.action.includes('Shoot')),targetConfirmed=dice.length>0){
    state.lastActivation={name:n.name,...decision,dice,answers,attackResolved,attackRequired,targetConfirmed};save();
    const targetOptions=eligibleNpoAttackTargets().map(id=>`<option value="${escapeHtml(id)}" ${state.npoAttackTargetId===id?'selected':''}>${escapeHtml(playerName(id))}</option>`).join('');
    const targetName=state.npoAttackTargetId?playerName(state.npoAttackTargetId):'';
    modalBody.innerHTML=`<div class="modal-inner ai-result">
      <p class="eyebrow">RECOMMENDED ACTIVATION</p>
      <div class="ai-result-title"><div><h2>${escapeHtml(n.name)}</h2><p>${escapeHtml(n.type)} · ${escapeHtml(n.behavior)}</p></div><span class="order-badge">${decision.stance}</span></div>
      <div class="activation-command"><small>ACTION SEQUENCE</small><strong>${escapeHtml(decision.action)}</strong></div>
      <div class="target-command"><small>TARGET PRIORITY</small><strong>${escapeHtml(decision.target)}</strong>${attackRequired?`<div class="field target-selection"><label for="npoPriorityTarget">Target Player Operative</label><select id="npoPriorityTarget" ${targetConfirmed||attackResolved?'disabled':''}><option value="">Select the operative matching this priority</option>${targetOptions}</select></div>`:''}</div>
      ${attackRequired&&!targetConfirmed?`<button class="btn secondary big-action" id="confirmNpoTarget" ${state.npoAttackTargetId?'':'disabled'}>Confirm Target</button><p class="validation-message">Confirm the target before rolling the NPO attack.</p>`:''}
      ${attackRequired&&targetConfirmed?`<h3>Attack Roll</h3><div class="dice-row ${attackResolved||!animateDice?'settled':'animated-roll'}" id="aiDice">${attackResolved||!animateDice?dice.map(dieHtml).join(''):dice.map(()=>rollingDieHtml()).join('')}</div><p id="aiDiceSummary" class="muted">${attackResolved?'Attack resolved.':animateDice?`Rolling ${dice.length} attack dice…`:initiativeSummary(dice)}</p>${!attackResolved?`<button class="btn secondary big-action" id="rollPlayerSaves">Roll Player Saves</button>`:''}`:''}
      ${attackResolved&&state.npoAttackSummary?`<section class="card npo-attack-summary">
        <p class="eyebrow">NPO ATTACK SUMMARY</p>
        <div class="combat-stage target-summary"><small>TARGET</small><strong>${escapeHtml(state.npoAttackSummary.targetName)}</strong></div>
        <div class="combat-stage"><small>PLAYER SAVE ROLL</small><div class="dice-row settled">${state.npoAttackSummary.saveDice.length?state.npoAttackSummary.saveDice.map(dieHtml).join(''):'<span class="muted">No save dice rolled</span>'}</div></div>
        <div class="damage-summary">
          <div><small>Unsaved normal hits</small><strong>${state.npoAttackSummary.normalRemaining}</strong></div>
          <div><small>Unsaved critical hits</small><strong>${state.npoAttackSummary.critRemaining}</strong></div>
          <div><small>Damage</small><strong>${state.npoAttackSummary.damage}</strong></div>
          <div><small>Player wounds</small><strong>${state.npoAttackSummary.before} → ${state.npoAttackSummary.after}</strong></div>
        </div>
      </section>`:''}
      ${attackRequired&&!attackResolved?'<p class="validation-message">Complete the attack before finishing this activation.</p>':''}
      <details class="decision-path"><summary>Why did the Guide choose this?</summary><p>${escapeHtml(decision.reason)}</p><ol>${decision.path.map(x=>`<li>${escapeHtml(x)}</li>`).join('')}</ol></details>
      <div class="wizard-actions"><button class="btn primary" id="completeNpo" ${attackRequired&&!attackResolved?'disabled':''}>Complete Activation</button></div>
    </div>`;
    if(!modal.open)modal.showModal();
    if(attackRequired&&targetConfirmed&&!attackResolved&&animateDice){setTimeout(()=>{const box=$('#aiDice');if(!box)return;box.innerHTML=dice.map(dieHtml).join('');box.classList.add('settled');$('#aiDiceSummary').textContent=initiativeSummary(dice);},850);}
    $('#npoPriorityTarget')?.addEventListener('change',()=>{state.npoAttackTargetId=$('#npoPriorityTarget').value||null;const b=$('#confirmNpoTarget');if(b)b.disabled=!state.npoAttackTargetId;save();});
    $('#confirmNpoTarget')?.addEventListener('click',()=>{
      if(!state.npoAttackTargetId)return;
      state.npoAttackSummary=null;
      const rolledDice=rollAttack(n.attack);
      const history=state.activationHistory.find(x=>x.side==='npo'&&x.label===n.name&&!x.target);
      if(history)history.target=playerName(state.npoAttackTargetId);
      log(`${n.name} confirmed ${playerName(state.npoAttackTargetId)} as the attack target and rolled the attack dice.`);
      save();
      renderNpoDecisionResult(n,decision,rolledDice,answers,false,true,true,true);
    });
    $('#rollPlayerSaves')?.addEventListener('click',()=>showNpoAttackWizard(n,dice,(summary)=>{
      state.npoAttackSummary=summary;
      save();
      showToast('NPO attack result recorded.');
      renderNpoDecisionResult(n,decision,dice,answers,true,false,true,true);
    },()=>{
      state.npoAttackTargetId=null;
      state.npoAttackSummary=null;
      save();
      renderNpoDecisionResult(n,decision,[],answers,false,false,true,false);
    }));
    $('#completeNpo').onclick=()=>{state.npoAttackTargetId=null;state.npoAttackSummary=null;save();closeModal();render();};
  }

  function showNpoAttackWizard(n,attackDice,onDone,onCancel){
    const target=selectedNpoAttackTarget();
    if(!target){showToast('Select the targeted Player operative first.');if(onCancel)onCancel();return;}
    showModal('NPO Attack Wizard',`<p>${escapeHtml(n.name)} is attacking <strong>${escapeHtml(target.name)}</strong>.</p>
      <div class="combat-stage"><small>NPO ATTACK DICE</small><div class="dice-row">${attackDice.map(dieHtml).join('')}</div><p>${n.attack.normal}/${n.attack.crit} damage · Hit ${n.attack.hit}+</p></div>
      <div class="combat-stage target-summary"><small>TARGET PLAYER OPERATIVE</small><strong>${escapeHtml(target.name)}</strong><p>${escapeHtml(target.type||target.role||'Player Operative')}</p></div>
      <div class="combat-grid">${spinnerField('playerDefenseDice','Player Defense Dice',3,0,6)}${spinnerField('playerSave','Player Save',target.save||3,2,6)}${spinnerField('npoAp','NPO AP',0,0,3)}${spinnerField('playerWounds','Player wounds remaining',target.wounds||10,1,30)}</div>
      <label class="check-row compact-check"><input type="checkbox" id="playerCover"><span><strong>Player retains one normal save for cover</strong></span></label>
      <div id="combatResults" class="combat-results"><p>Confirm the defense profile, then roll saves.</p></div>
      <div class="wizard-actions"><button class="btn ghost" id="cancelNpoAttack">Cancel</button><button class="btn primary" id="rollNpoSaves">Roll Player Saves</button></div>`);
    bindSpinners(modal);
    $('#cancelNpoAttack').onclick=()=>{save();if(onCancel)onCancel();};
    $('#rollNpoSaves').onclick=()=>{
      const before=num('playerWounds');
      const result=resolveDefense(attackDice,num('playerDefenseDice'),num('playerSave'),num('npoAp'),$('#playerCover').checked,n.attack);
      const after=Math.max(0,before-result.damage);
      $('#combatResults').innerHTML=`<div class="combat-stage"><small>PLAYER SAVE DICE</small><div class="dice-row animated-roll" id="playerSaveDiceResult">${result.saveDice.map(()=>rollingDieHtml()).join('')||'<span class="muted">No save dice rolled</span>'}</div>${result.coverRetained?'<span class="cover-retain">+ 1 retained normal cover save</span>':''}</div><div class="damage-summary"><div><small>Target</small><strong>${escapeHtml(target.name)}</strong></div><div><small>Unsaved normal hits</small><strong>${result.normalRemaining}</strong></div><div><small>Unsaved critical hits</small><strong>${result.critRemaining}</strong></div><div><small>Damage</small><strong>${result.damage}</strong></div><div><small>Player wounds</small><strong>${before} → ${after}</strong></div></div><p class="muted">Apply this wound change to ${escapeHtml(target.name)} on the tabletop.</p>`;
      $$('.combat-grid input, .combat-grid button',modal).forEach(el=>el.disabled=true);$('#playerCover').disabled=true;
      $('#rollNpoSaves').textContent='Apply Damage';
      $('#rollNpoSaves').onclick=()=>{
        const summary={
          targetId:state.npoAttackTargetId,
          targetName:target.name,
          attackDice:attackDice.map(d=>({...d})),
          saveDice:result.saveDice.map(d=>({...d})),
          normalRemaining:result.normalRemaining,
          critRemaining:result.critRemaining,
          damage:result.damage,
          before,
          after
        };
        log(`${n.name} dealt ${result.damage} damage to ${target.name} (${before} → ${after} wounds).`);
        save();
        if(onDone)onDone(summary);
      };
      setTimeout(()=>{const d=$('#playerSaveDiceResult');if(d&&result.saveDice.length){d.innerHTML=result.saveDice.map(dieHtml).join('');d.classList.add('settled');}},700);
    };
  }

  function resolveDefense(attackDice,defenseDice,saveTarget,ap,cover,damageProfile){
    let critRemaining=attackDice.filter(d=>d.kind==='crit').length;
    let normalRemaining=attackDice.filter(d=>d.kind==='hit').length;
    const count=Math.max(0,defenseDice-ap);
    const saveDice=Array.from({length:count},()=>{const value=roll();return{value,kind:value===6?'crit':value>=saveTarget?'save':'miss'};});
    let critSaves=saveDice.filter(d=>d.kind==='crit').length;
    let normalSaves=saveDice.filter(d=>d.kind==='save').length+(cover?1:0);
    const critCancelled=Math.min(critRemaining,critSaves);critRemaining-=critCancelled;critSaves-=critCancelled;
    const normalsByCrit=Math.min(normalRemaining,critSaves);normalRemaining-=normalsByCrit;
    const normalsCancelled=Math.min(normalRemaining,normalSaves);normalRemaining-=normalsCancelled;
    const damage=critRemaining*damageProfile.crit+normalRemaining*damageProfile.normal;
    return {saveDice,coverRetained:cover,critRemaining,normalRemaining,damage};
  }

  function spinnerField(id,label,value,min,max){return `<div class="field spinner-field"><label>${label}</label><div class="spinner"><input id="${id}" type="number" value="${value}" min="${min}" max="${max}" inputmode="numeric"><button type="button" data-spin="${id}" data-delta="-1" aria-label="Decrease ${label}">−</button><button type="button" data-spin="${id}" data-delta="1" aria-label="Increase ${label}">+</button></div></div>`;}
  function bindSpinners(root){$$('[data-spin]',root).forEach(b=>b.onclick=()=>{const input=$(`#${b.dataset.spin}`);const min=Number(input.min||0),max=Number(input.max||99);input.value=Math.max(min,Math.min(max,(Number(input.value)||0)+Number(b.dataset.delta)));});}
  function num(id){return Number($(`#${id}`)?.value)||0;}

  function rollingDieHtml(){
    const value=roll();
    return `<div class="die hit rolling" aria-label="Rolling die">${pipPositions[value].map(p=>`<span class="pip" style="grid-area:${Math.ceil(p/3)}/${((p-1)%3)+1}"></span>`).join('')}</div>`;
  }

  function rollAttack(profile){return Array.from({length:profile.dice},()=>{const value=roll();return{value,kind:value===6?'crit':value>=profile.hit?'hit':'miss'};});}
  const pipPositions={1:[5],2:[1,9],3:[1,5,9],4:[1,3,7,9],5:[1,3,5,7,9],6:[1,3,4,6,7,9]};
  function dieHtml(d){return `<div class="die ${d.kind}" aria-label="${d.value} ${d.kind}">${pipPositions[d.value].map(p=>`<span class="pip" style="grid-area:${Math.ceil(p/3)}/${((p-1)%3)+1}"></span>`).join('')}</div>`;}

  function renderMission(){
    const m=mission();
    const rules=(m.rules||[]).map(rule=>`<div class="mission-rule"><strong>${escapeHtml(rule.name)}</strong>${rule.timing?`<small>${escapeHtml(rule.timing)}</small>`:''}<p>${escapeHtml(rule.summary)}</p></div>`).join('');
    app.innerHTML=`<div class="panel-title"><div><p class="eyebrow">MISSION</p><h2>${m.number} · ${m.name}</h2><p>${m.brief}</p></div></div>
      <section class="card"><h3>Objective</h3><p>${m.objective}</p><div class="stat-grid"><div class="stat"><small>Starting NPOs</small><strong>${missionSetup(m)}</strong></div><div class="stat"><small>TP1 Initiative</small><strong>${missionFirstInitiative(m)==='npo'?'NPOs':'Player'}</strong></div><div class="stat"><small>${missionTracker(m)}</small><strong>${state.tracker} / ${missionTrackerMax(m)}</strong></div></div><p><strong>NPO deployment:</strong> ${escapeHtml(m.startingNpos?.deployment||'Use the mission rules.')}</p></section>
      ${boardSvg(m.id)}
      <section class="card"><h3>Mission rules</h3><div class="mission-rules">${rules}</div></section>
      <section class="card"><h3>Victory</h3><p><strong>Win:</strong> ${escapeHtml(m.victory?.win||'See mission rules.')}</p><p><strong>Lose:</strong> ${escapeHtml(m.victory?.lose||'See mission rules.')}</p></section>`;
  }
  function renderRoster(){app.innerHTML=`<div class="panel-title"><div><p class="eyebrow">NPO ROSTER</p><h2>${activeNpos().length} active NPOs</h2><p>Wounds and Ready status update the guided activation flow.</p></div><button class="btn secondary" id="addNpo">Add NPO</button></div><div class="roster-grid">${state.roster.length?state.roster.map(n=>operativeCard(n,true)).join(''):'<div class="card empty">No NPOs are currently on the battlefield.</div>'}</div>`;$('#addNpo').onclick=showAddNpo;$$('[data-player-attack]').forEach(b=>b.onclick=()=>showPlayerAttackWizard(b.dataset.playerAttack));$$('[data-wound]').forEach(b=>b.onclick=()=>adjustWounds(b.dataset.wound,-1));$$('[data-heal]').forEach(b=>b.onclick=()=>adjustWounds(b.dataset.heal,1));$$('[data-ready]').forEach(b=>b.onclick=()=>toggleReady(b.dataset.ready));$$('[data-delete]').forEach(b=>b.onclick=()=>deleteNpo(b.dataset.delete));}
  function operativeCard(n,controls){return `<article class="operative-card ${n.wounds<=0?'dead':''}"><h4>${escapeHtml(n.name)}</h4><p>${n.type} · ${n.behavior} · Save ${n.save}+</p><div class="wounds"><meter min="0" max="${n.maxWounds}" value="${n.wounds}"></meter><strong>${n.wounds}/${n.maxWounds}</strong></div><p>${n.ready&&n.wounds>0?'READY':'ACTIVATED'}</p>${controls?`<div class="quick-actions"><button class="btn secondary" data-player-attack="${n.id}">Player Attack</button><button class="btn ghost" data-wound="${n.id}">− Wound</button><button class="btn ghost" data-heal="${n.id}">+ Heal</button><button class="btn secondary" data-ready="${n.id}">${n.ready?'Expend':'Ready'}</button><button class="btn danger" data-delete="${n.id}">Delete</button></div>`:''}</article>`;}
  function renderJournal(){app.innerHTML=`<div class="panel-title"><div><p class="eyebrow">JOURNAL</p><h2>Battle Record</h2><p>Automatic game-state and Threat history.</p></div><button class="btn ghost" id="clearJournal">Clear</button></div><section class="card"><ol class="activity-log">${state.journal.length?state.journal.map(j=>`<li><time>${new Date(j.time).toLocaleString()}</time>${escapeHtml(j.text)}</li>`).join(''):'<li>No events recorded.</li>'}</ol></section>`;$('#clearJournal').onclick=()=>{state.journal=[];save();render();};}
  function renderHelp(){app.innerHTML=`<div class="panel-title"><div><p class="eyebrow">FIELD HELP</p><h2>Instructions & quick reference</h2><p>Review the NPO decision process and common gameplay terms without changing the current game.</p></div></div>${guideInstructionsHtml(false)}<section class="card help-list">
    <details><summary>What does Player mean?</summary><p>Your solo player-controlled Kill Team operatives.</p></details>
    <details><summary>What is an NPO?</summary><p>A non-player operative controlled by the Guide’s decision tree.</p></details>
    <details><summary>What is Threat Level?</summary><p>A 0–15 alert meter that rises from loud or destructive actions. Higher Threat produces higher grades, more reinforcements, and eventually Tomb World events.</p></details>
    <details><summary>What is Threat Grade?</summary><p>Grade 0 at Threat 0, Grade 1 at 1–5, Grade 2 at 6–10, and Grade 3 at 11–15. Reinforcements normally equal the current grade after Turning Point 1.</p></details>
    <details><summary>How does alternating activation work?</summary><p>The side with initiative activates first. The Guide then alternates Player and NPO activations whenever both sides still have ready operatives. If one side runs out, the other finishes its remaining activations.</p></details>
    <details><summary>What happens during the Strategy Phase?</summary><p>The Guide readies operatives, evaluates Threat Grade, generates reinforcements after Turning Point 1, checks for Tomb World events, and resolves initiative.</p></details>
    <details><summary>How are saves and damage handled?</summary><p>Attack dice and save dice are shown with visual pips. Saves cancel hits, and Player damage remains pending until the whole activation is confirmed.</p></details>
  </section>`;}


  function boardSvg(id){
    const currentMission=mission();
    const missionNumber=String(currentMission.number).padStart(2,'0');
    const imagePath=`Assets/Maps/mission-${missionNumber}.png`;
    return `<figure class="official-map-card">
      <div class="official-map-heading">
        <div><span>OFFICIAL MISSION MAP</span><strong>${escapeHtml(currentMission.number)} · ${escapeHtml(currentMission.name)}</strong></div>
        <small>Extracted from the included Games Workshop mission-pack PDF</small>
      </div>
      <img class="official-map-image" src="${imagePath}" alt="Official board layout for ${escapeHtml(currentMission.name)}" loading="eager">
      <figcaption>Only the map for this mission is shown. The complete official PDF is stored locally in <code>Assets/Tomb-World-Mission-Pack.pdf</code>.</figcaption>
    </figure>`;
  }

  function renderGuideMapMarker(marker){
    const [x,y,rawLabel]=marker;
    const label=escapeHtml(rawLabel);
    if(rawLabel==='SARCOPHAGUS') return `<g class="guide-map-marker guide-map-sarcophagus" transform="translate(${x} ${y})"><rect x="-58" y="-22" width="116" height="44" rx="12"/><path d="M-38 0H38"/><text y="5" text-anchor="middle">S</text><text class="guide-map-marker-caption" y="42" text-anchor="middle">SARCOPHAGUS</text></g>`;
    if(rawLabel==='ESCAPE') return `<g class="guide-map-marker guide-map-exit" transform="translate(${x-12} ${y})"><path d="M-36 -21H-8V-35L23 0-8 35V21H-36Z"/><text class="guide-map-marker-caption" x="-46" y="5" text-anchor="end">ESCAPE</text></g>`;
    if(rawLabel==='BREACH') return `<g class="guide-map-marker guide-map-breach" transform="translate(${x} ${y})"><circle r="17"/><path d="M-8 8 8-8M-8-8 8 8"/><text class="guide-map-marker-caption" y="38" text-anchor="middle">BREACH</text></g>`;
    if(rawLabel==='REGROUP') return `<g class="guide-map-marker guide-map-regroup" transform="translate(${x} ${y})"><circle r="27"/><path d="M-12 0H12M0-12V12"/><text class="guide-map-marker-caption" y="46" text-anchor="middle">REGROUP</text></g>`;
    return `<g class="guide-map-marker guide-map-objective" transform="translate(${x} ${y})"><path d="M0-18 18 0 0 18-18 0Z"/><text y="5" text-anchor="middle">${label}</text></g>`;
  }
  function rosterBreakdown(){const counts={};state.roster.forEach(n=>counts[n.type]=(counts[n.type]||0)+1);return Object.entries(counts).map(([k,v])=>`${v} ${k}${v>1?'s':''}`).join(' · ')||'No starting NPOs';}
  function showAddNpo(){showModal('Add NPO',`<div class="field"><label>NPO type</label><select id="newNpoType">${Object.keys(profiles).map(x=>`<option>${x}</option>`).join('')}</select></div><div class="wizard-actions"><button class="btn ghost" data-close>Cancel</button><button class="btn primary" id="confirmAdd">Add NPO</button></div>`);$('#confirmAdd').onclick=()=>{const type=$('#newNpoType').value,p=profiles[type];state.roster.push({id:uid(),name:`${type} ${state.roster.length+1}`,type,behavior:p.behavior,maxWounds:p.wounds,wounds:p.wounds,save:p.save,attack:{...p.attack},ready:true,deployed:true});log(`${type} added to the battlefield.`);closeModal();save();render();};}
  function adjustWounds(id,d){const n=state.roster.find(x=>x.id===id);if(!n)return;n.wounds=Math.max(0,Math.min(n.maxWounds,n.wounds+d));if(n.wounds===0)n.ready=false;save();render();}
  function toggleReady(id){const n=state.roster.find(x=>x.id===id);if(n&&n.wounds>0)n.ready=!n.ready;save();render();}
  function deleteNpo(id){state.roster=state.roster.filter(x=>x.id!==id);save();render();}

  function showModal(title,content,onClose){modalBody.innerHTML=`<div class="modal-inner"><h2>${title}</h2>${content}</div>`;if(!modal.open)modal.showModal();modal._onClose=onClose;$$('[data-close]',modal).forEach(b=>b.onclick=closeModal);}
  function closeModal(){
    if(modal.open)modal.close();
    const cb=modal._onClose;
    modal._onClose=null;
    if(cb)cb();
  }
  modal.addEventListener('cancel',e=>{e.preventDefault();closeModal();});

  function showToast(text){toast.textContent=text;toast.hidden=false;clearTimeout(showToast.t);showToast.t=setTimeout(()=>toast.hidden=true,6500);}
  function showGameMenu(){
    showModal('Game Menu',`<p>Open a reference screen without changing the guided play sequence, or begin a completely new game.</p>
      <div class="game-menu-grid">
        <button class="btn primary" data-game-view="play">Return to Guided Play</button>
        <button class="btn secondary" data-game-view="mission">Mission & Map</button>
        <button class="btn secondary" data-game-view="roster">NPO Roster</button>
        <button class="btn secondary" data-game-view="journal">Battle Journal</button>
        <button class="btn secondary" data-game-view="help">Help</button>
      </div>
      <div class="game-menu-session">
        <button class="btn ghost" id="menuExportSave">Export Save</button>
        <button class="btn ghost" id="menuImportSave">Import Save</button>
        <button class="btn danger" id="menuNewGame">Start New Game</button>
      </div>`);
    $$('[data-game-view]',modal).forEach(button=>button.onclick=()=>{
      state.tab=button.dataset.gameView;
      closeModal();
      save();
      render();
    });
    $('#menuExportSave').onclick=exportSave;
    $('#menuImportSave').onclick=()=>importInput.click();
    $('#menuNewGame').onclick=confirmNewGame;
  }

  function confirmNewGame(){showModal('Start New Game?',`<p>This will replace the current mission, roster, Threat, Turning Point, and Journal.</p><div class="wizard-actions"><button class="btn ghost" data-close>Cancel</button><button class="btn danger" id="confirmNewGame">Start New Game</button></div>`);$('#confirmNewGame').onclick=()=>{localStorage.removeItem(STORAGE_KEY);state=initialState();state.screen='setup';closeModal();save();render();};}
  function exportSave(){const blob=new Blob([JSON.stringify(state,null,2)],{type:'application/json'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='tomb-world-solo-guide-save.json';a.click();URL.revokeObjectURL(a.href);}
  importInput.addEventListener('change',async()=>{const f=importInput.files?.[0];if(!f)return;try{const data=JSON.parse(await f.text());if(!data.version)throw new Error();state=normalizeState(data);state.screen='game';save();render();showToast('Save imported.');}catch{showToast('That file is not a valid Tomb World Solo Guide save.');}finally{importInput.value='';}});

  function bindCommon(){
    const versionBadge=$('.version');
    if(versionBadge) versionBadge.textContent=`v${APP_VERSION}`;
    gameMenuBtn.onclick=showGameMenu;
  }

  Promise.all([loadMissionPack(),loadPlayerManifest()])
    .then(async ([,manifest])=>{
      const teams=manifest.teams||[];
      if(teams.length===1){
        state.playerTeamId=teams[0].id;
        await loadPlayerTeamData(teams[0].id);
      }else if(state.playerTeamId&&teams.some(team=>team.id===state.playerTeamId)){
        await loadPlayerTeamData(state.playerTeamId);
      }else{
        state.playerTeamId='';
        state.playerTeamFile='';
        playerTeamData=null;
      }
      render();
    })
    .catch(error=>{
      console.error(error);
      app.innerHTML=`<section class="card"><h2>Player operative data could not be loaded</h2><p>${escapeHtml(error.message)}</p><p>Run the app from a web server so it can load the mission and player-operative JSON files.</p></section>`;
      bindCommon();
    });
})();

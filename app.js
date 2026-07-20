(() => {
  'use strict';

  const STORAGE_KEY = 'tombWorldSoloGuide.v1';
  const APP_VERSION = '3.5.5';

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
  const updateNotice = $('#updateNotice');
  const updateAppBtn = $('#updateAppBtn');

  function registerServiceWorker(){
    if(!('serviceWorker' in navigator))return;
    let waitingWorker=null;
    let updateRequested=false;
    const showUpdate=worker=>{
      waitingWorker=worker;
      if(navigator.onLine)updateNotice.hidden=false;
    };
    window.addEventListener('online',()=>{
      if(waitingWorker)updateNotice.hidden=false;
    });
    updateAppBtn.addEventListener('click',()=>{
      if(!waitingWorker)return;
      updateRequested=true;
      updateAppBtn.disabled=true;
      waitingWorker.postMessage({type:'SKIP_WAITING'});
    });
    navigator.serviceWorker.addEventListener('controllerchange',()=>{
      if(updateRequested)window.location.reload();
    });
    window.addEventListener('load',()=>{
      navigator.serviceWorker.register('./service-worker.js',{scope:'./'})
        .then(registration=>{
          if(registration.waiting)showUpdate(registration.waiting);
          registration.addEventListener('updatefound',()=>{
            const installingWorker=registration.installing;
            if(!installingWorker)return;
            installingWorker.addEventListener('statechange',()=>{
              if(installingWorker.state==='installed'&&navigator.serviceWorker.controller){
                showUpdate(installingWorker);
              }
            });
          });
        })
        .catch(()=>{});
    });
  }

  registerServiceWorker();

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
  function playerCurrentWounds(id){
    const definition=playerDefinition(id);
    const stored=Number(state.playerWounds?.[id]);
    return Number.isFinite(stored)?stored:Number(definition?.wounds||0);
  }
  function livePlayerOperative(id){
    const definition=playerDefinition(id);
    return definition?{...definition,wounds:playerCurrentWounds(id)}:null;
  }
  function initializePlayerWounds(){
    state.playerWounds={};
    (state.playerRoster||[]).forEach(id=>{
      const definition=playerDefinition(id);
      if(definition)state.playerWounds[id]=Number(definition.wounds||0);
    });
  }
  function selectedPlayerOperatives(){return (state.playerRoster||[]).map(livePlayerOperative).filter(Boolean);}
  function playerRosterLimits(){
    const maxRoster=Number(playerTeamData?.maxRoster??playerTeamData?.rosterSize??5);
    const minRoster=Number(playerTeamData?.minRoster??maxRoster);
    return {minRoster,maxRoster};
  }
  function playerName(id){
    const definition=playerDefinition(id);
    if(!definition)return String(id);
    const baseName=definition.name||String(id);
    const matchingSelected=(state.playerRoster||[]).filter(selectedId=>playerDefinition(selectedId)?.name===baseName);
    if(matchingSelected.length<=1)return baseName;
    const index=matchingSelected.indexOf(id);
    return `${baseName} ${index>=0?index+1:1}`;
  }

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
    version:APP_VERSION, screen:'home', tab:'play', setupStep:0, missionId:null,
    setupChecks:[], roster:[], playerTeamId:'', playerTeamFile:'', playerRoster:[], playerRosterInitializedForTeamId:'', playerCount:0, playerReady:0, playerDeployed:false, turningPoint:0,
    threat:0, initiative:'player', phase:'setup', nextSide:'player', tracker:0,
    activeNpoId:null, journal:[], lastActivation:null, newIds:[], completed:false,
    strategyStage:null, strategyData:null, activationNumber:0,totalActivationsThisTP:0, playerActivated:0, npoActivated:0,
    activationHistory:[], playerActivatedIds:[], playerCasualtyIds:[], playerWounds:{}, reinforcementEntry:'Nearest valid entry point',
    gradeMilestone:null, tpStartThreat:0, tpStartGrade:0, tpStartDestroyedNpos:0, tpStartPlayerCasualties:0,
    npoAttackTargetId:null,
    npoAttackSummary:null, gameEnd:null
  });

  let state = normalizeState(load() || initialState());
  let lastRenderedStepKey = null;
  let threatAdjustOpen = false;
  let expandedRosterCategories = null;
  function autoSelectRequiredPlayerOperatives(){
    if(!playerTeamData||state.playerRosterInitializedForTeamId===playerTeamData.teamId)return;
    state.playerRosterInitializedForTeamId=playerTeamData.teamId;
    const operatives=playerTeamData.operatives||[];
    const requiredCategories=(playerTeamData.rosterCategories||[])
      .map(category=>({count:Number(category.requiredCount||0),eligible:operatives.filter(operative=>operative.category===category.id)}))
      .filter(category=>category.count>0);
    const selected=new Set(state.playerRoster||[]);
    requiredCategories.forEach(category=>{
      if(category.eligible.length===category.count)category.eligible.forEach(operative=>selected.add(operative.id));
    });
    state.playerRoster=[...selected];
    state.playerCount=state.playerRoster.length;
    state.playerReady=state.playerCount;
    initializePlayerWounds();
  }

  function save(){ state.version=APP_VERSION; localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); }
  function load(){ try{return JSON.parse(localStorage.getItem(STORAGE_KEY));}catch{return null;} }
  function normalizeState(raw){
    const base=initialState(), merged={...base,...raw};
    if(!['home','help','setup','game'].includes(merged.screen))merged.screen='home';
    if(!['play','mission','roster','player-roster','journal','help'].includes(merged.tab))merged.tab='play';
    merged.roster=Array.isArray(raw?.roster)?raw.roster:[];
    merged.journal=Array.isArray(raw?.journal)?raw.journal:[];
    merged.newIds=Array.isArray(raw?.newIds)?raw.newIds:[];
    merged.activationHistory=Array.isArray(raw?.activationHistory)?raw.activationHistory:[];
    merged.playerActivatedIds=Array.isArray(raw?.playerActivatedIds)?raw.playerActivatedIds:[];
    merged.playerCasualtyIds=Array.isArray(raw?.playerCasualtyIds)?raw.playerCasualtyIds:[];
    merged.playerWounds=raw?.playerWounds&&typeof raw.playerWounds==='object'?{...raw.playerWounds}:{};
    merged.playerRoster=Array.isArray(raw?.playerRoster)?raw.playerRoster:[];
    merged.playerTeamId=raw?.playerTeamId||'';
    merged.gameEnd=['victory','defeat'].includes(raw?.gameEnd)?raw.gameEnd:null;
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
  function livingPlayerOperativeCount(){
    const casualties=new Set(state.playerCasualtyIds||[]);
    return (state.playerRoster||[]).filter(id=>!casualties.has(id)).length;
  }

  function checkGameEnd(){
    const victory=state.roster.length>0&&activeNpos().length===0;
    const defeat=(state.playerRoster||[]).length>0&&livingPlayerOperativeCount()===0;
    if(!victory&&!defeat)return false;
    state.gameEnd=victory?'victory':'defeat';
    closeModal();
    save();
    render();
    return true;
  }

  function totalLivingOperatives(){
    return livingPlayerOperativeCount()+activeNpos().length;
  }

  function activationProgressLabel(){
    const current=Math.max(1,state.activationNumber+1);
    return `ACTIVATION ${current} OF ${totalLivingOperatives()}`;
  }

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
    return livePlayerOperative(state.npoAttackTargetId);
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
    sortOperativesGlobally();
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

    gameMenuBtn.hidden = state.screen !== 'game' || Boolean(state.gameEnd);
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
    $('#newGameBtn').onclick=()=>{ state=initialState(); state.screen='setup'; state.setupStep=0; expandedRosterCategories=null; save(); render(); };
    $('#continueBtn').onclick=()=>{ const saved=load(); if(saved){state=normalizeState(saved);state.screen='game';render();} };
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
    const cards=(playerManifest?.teams||[]).map(team=>`<button type="button" class="team-select-card ${state.playerTeamId===team.id?'selected':''}" data-player-team="${escapeHtml(team.id)}">
      <div class="team-select-card-head"><div><strong>${escapeHtml(team.name)}</strong><small>${escapeHtml(team.faction||'Kill Team')}</small></div>${state.playerTeamId===team.id?'<span>✓</span>':''}</div>
      <p>${escapeHtml(team.description||'')}</p>
    </button>`).join('');
    app.innerHTML=`<div class="wizard-shell"><div class="progress-head"><div><p class="eyebrow">NEW GAME SETUP</p><h2>Choose Kill Team</h2><p>Select the player-controlled Kill Team for this battle.</p></div></div><section class="wizard-card"><div class="team-select-grid">${cards}</div><div class="wizard-actions"><button class="btn ghost" id="teamSelectHome">Back</button></div></section></div>`;
    $('#teamSelectHome').onclick=()=>{state.screen='home';save();render();};
    $$('[data-player-team]').forEach(button=>button.onclick=async()=>{
      try{
        state.playerTeamId=button.dataset.playerTeam;
        state.playerRosterInitializedForTeamId='';
        state.playerRoster=[];
        state.playerCount=0;
        state.playerReady=0;
        state.playerCasualtyIds=[];
        state.playerWounds={};
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

  const setupStepDefinitions={
    mission:{title:'Choose Mission',subtitle:'Select the mission the Guide will run.'},
    killzone:{title:'Build the Killzone',subtitle:'Follow the board checklist before deploying models.'},
    team:{title:'Choose Player Kill Team',subtitle:'Select the player-controlled Kill Team for this battle.'},
    playerRoster:{title:'Build Player Roster',subtitle:'Choose the operatives you will use in this battle.'},
    npoRoster:{title:'Generate NPO Roster',subtitle:'The Guide uses the mission’s required starting formula.'},
    deploy:{title:'Deploy Kill Teams',subtitle:'Place both forces on the battlefield and confirm deployment.'},
    ready:{title:'Ready to Begin',subtitle:'Review the mission, then begin Turning Point 1.'}
  };
  function activeSetupSteps(){
    const steps=['mission','killzone'];
    if(hasMultiplePlayerTeams())steps.push('team');
    steps.push('playerRoster','npoRoster','deploy','ready');
    return steps;
  }
  function currentSetupStepId(){
    const steps=activeSetupSteps();
    state.setupStep=Math.max(0,Math.min(Number(state.setupStep||0),steps.length-1));
    return steps[state.setupStep];
  }
  function renderSetup(){
    const steps=activeSetupSteps();
    const stepId=currentSetupStepId();
    if(stepId==='playerRoster'){
      autoSelectRequiredPlayerOperatives();
      save();
    }
    if(stepId==='npoRoster'&&!state.roster.length){
      generateRoster();
      save();
    }
    const details=setupStepDefinitions[stepId];
    app.innerHTML=`<div class="wizard-shell"><div class="progress-head"><div><p class="eyebrow">NEW GAME SETUP</p><h2>${details.title}</h2><p>${details.subtitle}</p></div><div class="step-count">${state.setupStep+1} / ${steps.length}</div></div><div class="progress-bar"><span style="width:${((state.setupStep+1)/steps.length)*100}%"></span></div><section class="wizard-card">${setupContent(stepId)}</section></div>`;
    bindSetup(stepId);
  }
  function setupContent(stepId){
    if(stepId==='mission') return `<h3>Which mission are you playing?</h3><p>You can review the objective before committing.</p><div class="mission-list">${missions.map(m=>`<button class="mission-choice ${state.missionId===m.id?'selected':''}" data-mission="${m.id}"><div class="team-select-card-head"><div><small>${m.number}</small><strong>${m.name}</strong></div>${state.missionId===m.id?'<span>✓</span>':''}</div><span>${m.brief}</span></button>`).join('')}</div><div class="wizard-actions"><button class="btn ghost" id="setupHome">Back</button><button class="btn primary" id="setupNext" ${state.missionId?'':'disabled'}>Next</button></div>`;
    if(stepId==='killzone'){
      const m=mission();
      const checks=['Place walls and hatchways as shown','Place mission objective markers','Identify the Player drop zone','Identify NPO deployment areas'];
      const allChecked=checks.every((_,i)=>state.setupChecks[i]);
      return `<h3>${m.name} board setup</h3><p><strong>Objective:</strong> ${m.objective}</p>${boardSvg(m.id)}<div class="setup-bulk-row"><button class="btn secondary" id="checkAllSetup" ${allChecked?'disabled':''}>Check All</button></div><div class="checklist">${checks.map((c,i)=>`<label class="check-row"><input type="checkbox" data-check="${i}" ${state.setupChecks[i]?'checked':''}><span><strong>${c}</strong><small>${i===0?'Use the official mission map shown above to place the terrain and markers.':'Confirm this step on the physical board.'}</small></span></label>`).join('')}</div><div class="wizard-actions"><button class="btn ghost" id="setupBack">Back</button><button class="btn primary" id="setupNext" ${allChecked?'':'disabled'}>Board Ready</button></div>`;
    }
    if(stepId==='team'){
      const cards=(playerManifest?.teams||[]).map(team=>`<button type="button" class="team-select-card ${state.playerTeamId===team.id?'selected':''}" data-player-team="${escapeHtml(team.id)}"><div class="team-select-card-head"><div><strong>${escapeHtml(team.name)}</strong><small>${escapeHtml(team.faction||'Kill Team')}</small></div>${state.playerTeamId===team.id?'<span>✓</span>':''}</div><p>${escapeHtml(team.description||'')}</p></button>`).join('');
      return `<h3>Which Kill Team are you playing?</h3><p>Your choice determines the operatives available on the next step.</p><div class="team-select-grid">${cards}</div><div class="wizard-actions"><button class="btn ghost" id="setupBack">Back</button><button class="btn primary" id="setupNext" ${state.playerTeamId?'':'disabled'}>Build Roster</button></div>`;
    }
    if(stepId==='playerRoster'){
      const selected=new Set(state.playerRoster||[]);
      const selectedDefs=selectedPlayerOperatives();
      const gravisCount=selectedDefs.filter(o=>o.gravis).length;
      const gunnerCount=selectedDefs.filter(o=>o.role==='Gunner').length;
      const trooperCount=selectedDefs.filter(o=>o.role==='Trooper').length;
      const maxGunners=Number(playerTeamData?.selectionRules?.maxGunners||Infinity);
      const maxGravis=Number(playerTeamData?.selectionRules?.maxGravis||1);
      const mandatoryTroopers=Number(playerTeamData?.selectionRules?.mandatoryTroopers||0);
      const requiredLeaderId=playerTeamData?.selectionRules?.leader?.operativeId||'';
      const leaderSelected=!requiredLeaderId||selected.has(requiredLeaderId);
      const requiredLeaderCategory=(playerTeamData?.rosterCategories||[]).find(category=>category.id==='leader'&&Number(category.requiredCount||0)>0);
      const requiredLeaderCount=requiredLeaderId?Number(playerTeamData?.selectionRules?.leader?.count||1):Number(requiredLeaderCategory?.requiredCount||0);
      const selectedLeaderCount=requiredLeaderId
        ? (leaderSelected?1:0)
        : (playerTeamData?.operatives||[]).filter(operative=>operative.category==='leader'&&selected.has(operative.id)).length;
      const requiredLeaderSelected=requiredLeaderId
        ? leaderSelected
        : selectedLeaderCount>=requiredLeaderCount;
      const hasGravis=(playerTeamData?.operatives||[]).some(o=>o.gravis);
      const {minRoster,maxRoster}=playerRosterLimits();
      const categoryMetadata=new Map((playerTeamData?.rosterCategories||[]).map(category=>[category.id,category]));
      const categories=[];
      (playerTeamData?.operatives||[]).forEach(operative=>{
        const categoryId=operative.category;
        let category=categories.find(entry=>entry.id===categoryId);
        if(!category){
          const metadata=categoryMetadata.get(categoryId)||{};
          category={id:categoryId,label:metadata.label||categoryId,order:Number(metadata.order??categories.length),operatives:[]};
          categories.push(category);
        }
        category.operatives.push(operative);
      });
      categories.sort((a,b)=>a.label.localeCompare(b.label));
      if(expandedRosterCategories===null)expandedRosterCategories=new Set();
      const sections=categories.map((category,index)=>{
        const categorySelected=category.operatives.filter(operative=>selected.has(operative.id)).length;
        const expanded=expandedRosterCategories.has(category.id);
        const panelId=`roster-category-${index}`;
        const cards=category.operatives.map(o=>{
          const chosen=selected.has(o.id);
          const rosterBlocked=!chosen&&selected.size>=maxRoster;
          const gravisBlocked=!chosen&&o.gravis&&gravisCount>=maxGravis;
          const gunnerBlocked=!chosen&&o.role==='Gunner'&&gunnerCount>=maxGunners;
          return `<button type="button" class="player-roster-card ${chosen?'selected':''}" data-select-player="${o.id}" ${rosterBlocked||gravisBlocked||gunnerBlocked?'disabled':''}><div class="player-roster-card-head"><div><strong>${escapeHtml(o.name)}</strong><small>${escapeHtml(o.role)}${o.gravis?' · GRAVIS':''}</small></div><span>${chosen?'✓':'+'}</span></div><div class="operative-stat-line"><span><small>APL</small><b>${o.apl}</b></span><span><small>MOVE</small><b>${o.move}"</b></span><span><small>SAVE</small><b>${o.save}+</b></span><span><small>WOUNDS</small><b>${o.wounds}</b></span></div></button>`;
        }).join('');
        return `<section class="roster-category"><button type="button" class="roster-category-heading" data-roster-category-toggle="${escapeHtml(category.id)}" aria-expanded="${expanded}" aria-controls="${panelId}"><span class="roster-category-title"><span class="roster-category-indicator" aria-hidden="true">›</span>${escapeHtml(category.label)}</span><span>${categorySelected} selected</span></button><div class="player-roster-grid roster-category-content" id="${panelId}" ${expanded?'':'hidden'}>${cards}</div></section>`;
      }).join('');
      const selectionPrompt=minRoster===maxRoster?`Select exactly ${maxRoster} operatives.`:`Select between ${minRoster} and ${maxRoster} operatives.`;
      const selectionCount=minRoster===maxRoster?`Total Operatives: ${selected.size} of ${maxRoster}`:`Total Operatives: ${selected.size} of ${maxRoster} (minimum ${minRoster})`;
      const requirements=[];
      if(hasGravis)requirements.push(`Required Gravis: ${gravisCount} of 1`);
      if(Number.isFinite(maxGunners))requirements.push(`Maximum Gunners: ${gunnerCount} of ${maxGunners}`);
      if(requiredLeaderId||requiredLeaderCategory)requirements.push(`Required Leader: ${selectedLeaderCount} of ${requiredLeaderCount}`);
      if(mandatoryTroopers)requirements.push(`Required Troopers: ${trooperCount} of ${mandatoryTroopers}`);
      requirements.push(selectionCount);
      const valid=requiredLeaderSelected&&gunnerCount<=maxGunners&&trooperCount>=mandatoryTroopers&&(!hasGravis||(gravisCount>=1&&gravisCount<=maxGravis))&&selected.size>=minRoster&&selected.size<=maxRoster;
      const requirementItems=requirements.map(requirement=>`<li>${escapeHtml(requirement)}</li>`).join('');
      return `<h3>Choose your ${escapeHtml(playerTeamData?.teamName||playerTeamEntry()?.name||'Kill Team')} roster</h3><p>${selectionPrompt}</p><section class="player-roster-summary" aria-labelledby="roster-requirements-heading"><h4 id="roster-requirements-heading">Roster Requirements</h4><ul>${requirementItems}</ul></section><div class="roster-categories">${sections}</div>${selectedDefs.length?`<div class="summary-box"><strong>Selected roster</strong><br>${selectedDefs.map(o=>escapeHtml(o.name)).join(' · ')}</div>`:''}<div class="wizard-actions"><button class="btn ghost" id="setupBack">Back</button><button class="btn primary" id="setupNext" ${valid?'':'disabled'}>Roster Ready</button></div>`;
    }
    if(stepId==='npoRoster'){
      const m=mission();
      const noStartingNpos=missionSetup(m)==='0';
      const rosterContent=state.roster.length
        ? `<div class="summary-box"><strong>${state.roster.length} NPOs generated automatically</strong><br>${rosterBreakdown()}</div><div class="player-roster-grid npo-setup-grid">${state.roster.map(n=>npoRosterCard(n,false)).join('')}</div>`
        : `<div class="no-npo-message"><strong>The battle begins with no deployed NPOs.</strong><span>The first NPOs will enter play through the mission's reinforcement rules.</span></div>`;
      return `<h3>Mission starting roster</h3><p>${m.name} begins with <strong>${missionSetup(m)}</strong> NPOs.</p>${rosterContent}<div class="wizard-actions ${noStartingNpos?'two-actions':''}"><button class="btn ghost" id="setupBack">Back</button>${noStartingNpos?'':`<button class="btn secondary" id="generateBtn">Regenerate Roster</button>`}<button class="btn primary" id="setupNext" ${state.roster.length||noStartingNpos?'':'disabled'}>Continue</button></div>`;
    }
    if(stepId==='deploy'){
      const allNposPlaced=state.roster.every(n=>n.deployed);
      const {minRoster,maxRoster}=playerRosterLimits();
      const playerValid=(state.playerRoster||[]).length>=minRoster&&(state.playerRoster||[]).length<=maxRoster;
      return `<h3>Deploy Kill Teams</h3><p>Place both forces in their mission deployment zones, then confirm each side is ready.</p><div class="checklist"><label class="check-row"><input id="playerDeployed" type="checkbox" ${state.playerDeployed?'checked':''} ${playerValid?'':'disabled'}><span><strong>${escapeHtml(playerTeamData?.teamName||playerTeamEntry()?.name||'Player')} Kill Team deployed</strong><small>All selected Player operatives are on the battlefield.</small></span></label><label class="check-row"><input id="npoDeployed" type="checkbox" ${allNposPlaced?'checked':''}><span><strong>Necron Kill Team deployed</strong><small>${state.roster.length?'All starting NPO operatives are on the battlefield.':'No starting NPO deployment is required for this mission.'}</small></span></label></div><div class="wizard-actions"><button class="btn ghost" id="setupBack">Back</button><button class="btn primary" id="setupNext" ${playerValid&&state.playerDeployed&&allNposPlaced?'':'disabled'}>Deployment Complete</button></div>`;
    }
    const m=mission();
    const rules=(m.rules||[]).map(rule=>`<div class="mission-rule"><strong>${escapeHtml(rule.name||'Special Rule')}</strong>${rule.timing?`<small>${escapeHtml(rule.timing)}</small>`:''}<p>${escapeHtml(rule.summary||'')}</p></div>`).join('');
    return `<h3>Mission Briefing</h3><div class="mission-briefing"><div class="mission-briefing-section mission-heading"><span>Mission</span><strong>${escapeHtml(m.number)} · ${escapeHtml(m.name)}</strong></div><div class="mission-briefing-section"><h4>Objective</h4><p>${escapeHtml(m.objective)}</p></div><div class="mission-briefing-section"><h4>Special Rules</h4>${rules||`<p>${escapeHtml(missionSpecial())}</p>`}</div></div><div class="wizard-actions"><button class="btn ghost" id="setupBack">Back</button><button class="btn primary" id="beginGame">Begin Turning Point 1</button></div>`;
  }

  function bindSetup(stepId){
    $$('.mission-choice').forEach(b=>b.onclick=()=>{state.missionId=b.dataset.mission;state.setupChecks=[];state.roster=[];save();render();});
    $('#setupHome')?.addEventListener('click',()=>{state.screen='home';save();render();});
    $('#setupBack')?.addEventListener('click',()=>{state.setupStep=Math.max(0,state.setupStep-1);save();render();});
    $('#setupNext')?.addEventListener('click',()=>{const steps=activeSetupSteps();state.setupStep=Math.min(steps.length-1,state.setupStep+1);save();render();});
    $$('[data-player-team]').forEach(button=>button.onclick=async()=>{
      try{
        if(state.playerTeamId!==button.dataset.playerTeam){
          state.playerTeamId=button.dataset.playerTeam;
          state.playerRosterInitializedForTeamId='';
          state.playerRoster=[];state.playerCount=0;state.playerReady=0;state.playerCasualtyIds=[];state.playerWounds={};state.playerActivatedIds=[];state.playerDeployed=false;
          await loadPlayerTeamData(state.playerTeamId);
        }
        save();render();
      }catch(error){console.error(error);showToast(error.message);}
    });
    $$('[data-check]').forEach(c=>c.onchange=()=>{state.setupChecks[Number(c.dataset.check)]=c.checked;save();render();});
    $('#checkAllSetup')?.addEventListener('click',()=>{state.setupChecks=[true,true,true,true];save();render();});
    $('#generateBtn')?.addEventListener('click',()=>{generateRoster();save();render();});
    $('#npoDeployed')?.addEventListener('change',e=>{state.roster.forEach(n=>n.deployed=e.target.checked);save();render();});
    $$('[data-roster-category-toggle]').forEach(button=>button.addEventListener('click',()=>{
      const expanded=button.getAttribute('aria-expanded')==='true';
      if(expanded)expandedRosterCategories.delete(button.dataset.rosterCategoryToggle);
      else expandedRosterCategories.add(button.dataset.rosterCategoryToggle);
      button.setAttribute('aria-expanded',String(!expanded));
      const content=document.getElementById(button.getAttribute('aria-controls'));
      if(content)content.hidden=expanded;
    }));
    $$('[data-select-player]').forEach(button=>button.addEventListener('click',()=>{
      const id=button.dataset.selectPlayer;
      const selected=new Set(state.playerRoster||[]);
      if(selected.has(id))selected.delete(id);
      else if(selected.size<playerRosterLimits().maxRoster){
        const candidate=playerDefinition(id);
        if(candidate?.gravis&&selectedPlayerOperatives().some(o=>o.gravis)){showToast('This Kill Team can include only one Gravis operative.');return;}
        const maxGunners=Number(playerTeamData?.selectionRules?.maxGunners||Infinity);
        if(candidate?.role==='Gunner'&&selectedPlayerOperatives().filter(o=>o.role==='Gunner').length>=maxGunners){showToast(`This Kill Team can include only ${maxGunners} Gunners.`);return;}
        selected.add(id);
      }
      state.playerRoster=[...selected];
      state.playerCount=state.playerRoster.length;state.playerReady=state.playerCount;state.playerCasualtyIds=[];initializePlayerWounds();state.playerActivatedIds=[];state.playerDeployed=false;
      save();render();
    }));
    $('#playerDeployed')?.addEventListener('change',e=>{state.playerDeployed=e.target.checked;save();render();});
    $('#beginGame')?.addEventListener('click',()=>{
      state.screen='game';state.tab='play';state.turningPoint=0;state.phase='between';state.nextSide='player';state.playerCount=(state.playerRoster||[]).length;state.playerReady=state.playerCount;
      if(!state.playerWounds||Object.keys(state.playerWounds).length===0)initializePlayerWounds();
      state.roster.forEach(n=>n.ready=false);log(`Mission started: ${mission().name}.`);startTurningPoint();
    });
  }

  function renderGame(){
    if(state.gameEnd){
      const victory=state.gameEnd==='victory';
      app.innerHTML=`<section class="hero-card"><p class="eyebrow">GAME OVER</p><img class="game-end-image" src="Assets/Images/${victory?'victory':'defeat'}.png" alt="${victory?'Victory':'Defeat'}"><p>${victory?'All NPO operatives have been eliminated.':'Your kill team has been eliminated.'}</p><div class="button-row"><button class="btn primary" id="gameEndNewGame">Start New Game</button></div></section>`;
      $('#gameEndNewGame').onclick=confirmNewGame;
      return;
    }
    if(state.tab==='play') renderPlay();
    else if(state.tab==='mission') renderMission();
    else if(state.tab==='roster') renderRoster();
    else if(state.tab==='player-roster') renderPlayerRoster();
    else if(state.tab==='journal') renderJournal();
    else renderHelp();

    if(state.tab!=='play'){
      app.insertAdjacentHTML('afterbegin',`<div class="reference-return"><button class="btn primary" id="returnToGuide">Return to Guided Play</button><small>Reference screens do not change the current Turning Point or activation state.</small></div>`);
      $('#returnToGuide').onclick=()=>{state.tab='play';save();render();};
    }
  }

  function hud(){return `<div class="hud"><div><small>Turning<span class="portrait-break"><br></span> Point</small><strong>${state.turningPoint||'Setup'}</strong></div><button class="hud-cell hud-threat" id="threatHudToggle" type="button" aria-expanded="${threatAdjustOpen}" aria-controls="threatAdjuster"><small>Threat<span class="portrait-break"><br></span> Level</small><strong>${state.threat}</strong></button><div><small>Grade<span class="portrait-break"><br></span> Level</small><strong>${threatGrade()}</strong></div><div><small>Player<span class="portrait-break"><br></span> Ready</small><strong>${state.playerReady}</strong></div><div><small>NPO<span class="portrait-break"><br></span> Ready</small><strong>${readyNpos().length}</strong></div></div><div class="threat-strip ${threatAdjustOpen?'':'hidden'}" id="threatAdjuster"><div><strong>THREAT LEVEL: ${threatLabel()}</strong><small>${threatGrade()===3?'Maximum Grade':`Next Grade at Threat Level ${[1,6,11][threatGrade()]}`}</small></div><div class="threat-meter"><span style="width:${(state.threat/15)*100}%"></span></div><button class="mini-btn" id="threatDown" aria-label="Decrease Threat">−</button><button class="mini-btn" id="threatUp" aria-label="Increase Threat">+</button></div>`;}

  function renderPlay(){
    const milestone=state.gradeMilestone?`<section class="grade-milestone"><div><small>THREAT ESCALATION</small><strong>Grade ${state.gradeMilestone.grade}: ${escapeHtml(state.gradeMilestone.label)}</strong><span>Threat has reached Level ${state.gradeMilestone.threat}.</span></div><button class="btn ghost compact" id="dismissGradeMilestone">Dismiss</button></section>`:'';
    app.innerHTML=hud()+milestone+`<div class="phase-track"><span class="${state.phase==='strategy'?'current':''}">Strategy</span>›<span class="${state.phase==='firefight'?'current':''}">Activations</span>›<span class="${state.phase==='end'?'current':''}">End Turning Point</span></div>${nextStepCard()}${state.phase==='firefight'?activationTracker():''}`;
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
    if(state.nextSide==='player' && playerOperativesRemaining()>0) return `<section class="next-card"><span class="phase">FIREFIGHT PHASE · ${activationProgressLabel()}</span><h2>Player Activation</h2><p>Activate one Player operative on the tabletop. After it completes, the Guide will alternate to an NPO if one is ready.</p><button class="btn primary big-action" id="playerActivation">Activate an Operative</button></section>`;
    if(state.nextSide==='npo' && readyNpos().length>0){const n=nextNpo();return `<section class="next-card npo-activation-card"><span class="phase">NPO ACTIVATION · ${activationProgressLabel()}</span><h2 class="npo-activation-title">${escapeHtml(npoName(n))}</h2><p class="npo-activation-meta">${escapeHtml(n.behavior)} · ${n.wounds}/${n.maxWounds} wounds</p><button class="btn primary big-action" id="npoActivation">Activate NPO</button></section>`;}
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
      return `<section class="next-card"><span class="phase">STRATEGY PHASE · STEP 1 OF 2</span><h2>Complete the Strategy Phase</h2><p class="strategy-intro">Before continuing to initiative, complete the tabletop Strategy Phase for Turning Point ${state.turningPoint}.</p><div class="strategy-phase-guide"><ol><li>Generate Command Points (CP) as required by the game rules.</li><li>Play any Strategic Ploys you want to use this Turning Point.</li><li>Resolve abilities and mission rules that occur during the Strategy Phase.</li><li>Review the Guide's Threat, reinforcement, and Tomb World event results below.</li></ol><p>When all Strategy Phase actions are complete, continue to initiative.</p></div><div class="stat-grid strategy-stat-grid"><div class="stat tooltip-stat" tabindex="0" data-tooltip="Threat rises from loud or aggressive actions. Higher Threat can increase the Grade, reinforcements, and Tomb World events."><small>THREAT LEVEL <span class="info-dot">i</span></small><strong>${state.threat}</strong></div><div class="stat tooltip-stat" tabindex="0" data-tooltip="Grade 0–3 is derived from Threat and determines reinforcement pressure and some events."><small>GRADE LEVEL <span class="info-dot">i</span></small><strong>${threatGrade()}</strong></div><div class="stat tooltip-stat" tabindex="0" data-tooltip="The number of living NPOs that are Ready and may still activate during this Turning Point."><small>NPOs Ready <span class="info-dot">i</span></small><strong>${readyNpos().length}</strong></div><div class="stat tooltip-stat" tabindex="0" data-tooltip="Additional NPOs generated during this Strategy Phase. Battlefield limits may block some arrivals."><small>Reinforcements <span class="info-dot">i</span></small><strong>${(d.reinforcements||[]).length}</strong></div></div>${rolls?`<h3>Reinforcements generated</h3><div class="reinforcement-grid">${rolls}</div><div class="field"><label>Reinforcement entry point</label><select id="reinforcementEntry"><option ${state.reinforcementEntry==='Nearest valid entry point'?'selected':''}>Nearest valid entry point</option><option ${state.reinforcementEntry==='Entry Point A'?'selected':''}>Entry Point A</option><option ${state.reinforcementEntry==='Entry Point B'?'selected':''}>Entry Point B</option><option ${state.reinforcementEntry==='Entry Point C'?'selected':''}>Entry Point C</option><option ${state.reinforcementEntry==='Custom placement'?'selected':''}>Custom placement</option></select></div>`:'<div class="summary-box"><strong>No reinforcements arrive.</strong></div>'}${d.blocked?`<p class="warning-text">${d.blocked} reinforcement(s) were blocked by the 10-NPO battlefield limit.</p>`:''}${d.event?`<div class="summary-box"><strong>${d.event[0]}</strong><br>${d.event[1]}</div>`:'<p>No Tomb World event is required.</p>'}<button class="btn primary big-action" id="continueStrategy">Strategy Phase Complete</button></section>`;
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
    const npoRows=state.roster.map(n=>{
      const eliminated=n.wounds<=0;
      const status=eliminated?'ELIMINATED':n.ready?'READY':'ACTIVATED';
      const cls=eliminated?'eliminated':n.ready?'ready':'activated';
      return `<div class="tracker-operative npo ${cls}"><span>${escapeHtml(npoName(n))}</span><strong>${status}</strong></div>`;
    }).join('');
    return `<section class="card activation-tracker"><details class="activation-details">
      <summary><div><p class="eyebrow">ACTIVATION TRACKER</p><h3>${state.activationNumber} activations completed</h3></div><div class="turn-badge">Next: ${state.nextSide==='npo'?'NPO':'Player'}</div></summary>
      <div class="activation-details-content">
      <div class="tracker-section">
        <small>${escapeHtml(playerTeamData?.teamName||playerTeamEntry()?.name||'Player')} operatives</small>
        <p class="muted compact-copy">All selected operatives are listed, including eliminated operatives. Select a Player operative to mark it eliminated or restore it.</p>
        <div class="tracker-operative-grid">${playerRows||'<span class="muted">No player operatives selected</span>'}</div>
      </div>
      <div class="tracker-section">
        <small>NPOs</small>
        <div class="tracker-operative-grid">${npoRows||'<span class="muted">No NPO operatives generated</span>'}</div>
      </div>
      </div>
    </details></section>`;
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
      state.playerWounds=state.playerWounds||{};
      if(ids.has(operativeId)){
        ids.delete(operativeId);
        state.playerWounds[operativeId]=Number(playerDefinition(operativeId)?.wounds||0);
        log(`${operativeName} restored.`);
      }else{
        ids.add(operativeId);
        state.playerWounds[operativeId]=0;
        if(!state.playerActivatedIds.includes(operativeId))state.playerActivatedIds.push(operativeId);
        log(`${operativeName} eliminated.`);
      }
      state.playerCasualtyIds=[...ids];
      state.playerReady=playerOperativesRemaining();
      if(checkGameEnd())return;
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
    $('#reinforcementEntry')?.addEventListener('change',e=>{state.reinforcementEntry=e.target.value;save();});
    $('#continueStrategy')?.addEventListener('click',()=>{state.reinforcementEntry=$('#reinforcementEntry')?.value||state.reinforcementEntry;state.strategyStage='initiative';initiativeRolling=state.turningPoint!==1;save();render();if(initiativeRolling)animateInitiativeResult();});
    $('#rerollInitiative')?.addEventListener('click',()=>{rollInitiative();initiativeRolling=true;save();render();animateInitiativeResult();});
    $$('[data-init]').forEach(b=>b.onclick=()=>beginFirefight(b.dataset.init));
    $('#playerActivation')?.addEventListener('click',()=>showPlayerActivation());
    $('#npoActivation')?.addEventListener('click',showNpoWizard);
    $('#tracker')?.addEventListener('change',e=>{state.tracker=Math.max(0,Math.min(missionTrackerMax(),Number(e.target.value)||0));save();});
    $('#endChecked')?.addEventListener('change',e=>{$('#finishTp').disabled=!e.target.checked;});
    $('#finishTp')?.addEventListener('click',()=>{
      log(`Turning Point ${state.turningPoint} completed.`);
      state.strategyStage=null;
      state.strategyData=null;
      state.newIds=[];
      if(state.turningPoint>=4){
        state.completed=true;
        state.phase='end';
        log('Mission complete after Turning Point 4.');
      }else{
        state.phase='between';
      }
      save();render();
    });
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
      state.strategyData.suggestedInitiative=missionFirstInitiative();
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
    const selectedOperative=playerDefinition(selectedId);
    const moveDistance=Number(selectedOperative?.move||6);
    const chargeDistance=moveDistance+2;
    const dashDistance=3;
    const fallBackDistance=moveDistance;
    const shootPending=stage.pendingShoot||null;
    const meleePending=stage.pendingMelee||null;

    showModal('Activate an Operative',`
      <p>Choose the Player operative being activated. That operative cannot activate again during this Turning Point after the activation is confirmed.</p>
      <div class="field">
        <label>Player operative</label>
        <select id="playerOperativeSelect">
          <option value="">Select a Player operative...</option>
          ${remaining.map(id=>`<option value="${id}" ${selectedId===id?'selected':''}>${escapeHtml(playerName(id))}</option>`).join('')}
        </select>
      </div>
      <fieldset id="playerActivationControls" class="${selectedId?'':'inactive'}" aria-disabled="${selectedId?'false':'true'}">
        <div class="activation-apl-bar ap-usage-only">
          <div class="ap-usage" id="apUsage"><small>AP used</small><strong>0 / ${Number(stage.apl||playerDefinition(selectedId)?.apl||3)}</strong></div>
        </div>
        <div id="apWarning" class="warning-text hidden"></div>
        <p class="muted">Select everything this operative will do. Shooting and Melee attacks are resolved only after you press Complete Activation.</p>
        <div class="activation-groups">
          <section class="activation-group">
            <div class="activation-group-title"><span>↔</span><div><strong>Movement</strong><small>Position and control actions</small></div></div>
            <div class="toggle-list player-action-list">
              <label><input type="checkbox" id="eaMove" ${checked('move')}><span>Move <small>▲ ${moveDistance}&quot; · 1 AP</small></span></label>
              <label><input type="checkbox" id="eaDash" ${checked('dash')}><span>Dash <small>▲ ${dashDistance}&quot; · 1 AP</small></span></label>
              <label><input type="checkbox" id="eaCharge" ${checked('charge')}><span>Charge <small>▲ ${chargeDistance}&quot; · 1 AP</small></span></label>
              <label><input type="checkbox" id="eaFallBack" ${checked('fallBack')}><span>Fall Back <small>▲ ${fallBackDistance}&quot; · 2 AP</small></span></label>
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

    // iOS Safari can retain focus on the button that opened the dialog,
    // which occasionally prevents the native select from opening on first tap.
    requestAnimationFrame(()=>{
      modal.scrollTop=0;
      modalBody.scrollTop=0;
      if(document.activeElement!==modal){
        try{modal.focus({preventScroll:true});}catch{modal.focus();}
      }
      operativeSelect.style.pointerEvents='none';
      requestAnimationFrame(()=>{operativeSelect.style.pointerEvents='';});
    });
    operativeSelect.addEventListener('change',()=>{
      const selectedOperative=playerDefinition(operativeSelect.value);const updated={...stage,playerOperativeId:operativeSelect.value||'',apl:Number(selectedOperative?.apl||stage.apl||3)};
      showPlayerActivation(updated);
    });

    const actionIds=['eaMove','eaDash','eaCharge','eaFallBack','eaShoot','eaMelee','eaDamage','eaHatch','eaBreach','eaObjective'];
    const clearPass=()=>{if($('#eaPass'))$('#eaPass').checked=false;};

    function updatePlayerActionAvailability(){
      const current=readPlayerActivationStage(stage);
      const apl=Number(playerDefinition(current.playerOperativeId)?.apl||current.apl||3);
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
      apl:Number(playerDefinition(previous.playerOperativeId)?.apl||previous.apl||3),
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
      showPendingPlayerAttackWizard(
        stage,
        'shoot',
        result=>resolvePendingPlayerAttacks({...stage,pendingShoot:result}),
        ()=>showPlayerActivation(stage)
      );
      return;
    }
    if(stage.melee&&!stage.pendingMelee){
      const remainingTargets=activeNpos().filter(n=>projectedNpoWounds(n.id,stage)>0);
      if(!remainingTargets.length){
        resolvePendingPlayerAttacks({...stage,melee:false,meleeSkipped:true});
        return;
      }
      showPendingPlayerAttackWizard(
        stage,
        'melee',
        result=>resolvePendingPlayerAttacks({...stage,pendingMelee:result}),
        ()=>showPlayerActivation(stage),
        ()=>resolvePendingPlayerAttacks({...stage,melee:false,meleeSkipped:true})
      );
      return;
    }
    showPlayerActivationConfirmation(stage);
  }

  function showPlayerActivationConfirmation(stage){
    const pending=[stage.pendingShoot,stage.pendingMelee].filter(Boolean);
    const eliminated=pending.filter(p=>Number(p.after)<=0);
    const eliminationBanner=eliminated.length?`<section class="elimination-banner" aria-label="NPO eliminated">
      <span class="elimination-icon" aria-hidden="true">☠</span>
      <div><small>NPO ELIMINATED</small><strong>${eliminated.map(p=>escapeHtml(p.targetName)).join(', ')}</strong></div>
    </section>`:'';
    const attackRows=pending.map(p=>{
      const lethal=Number(p.after)<=0;
      return `<section class="attack-confirmation-card ${lethal?'eliminated':''}">
        <div class="attack-confirmation-heading">
          <small>${p.attackType==='shoot'?'SHOOTING':'MELEE'}</small>
          ${lethal?'<span class="eliminated-badge">☠ ELIMINATED</span>':''}
        </div>
        <strong class="attack-confirmation-target">${escapeHtml(p.targetName)}</strong>
        <div class="attack-confirmation-stats">
          <div><small>Damage</small><strong>${p.damage}</strong></div>
          <div><small>Wounds</small><strong>${p.before} → <span class="${lethal?'zero-wounds':''}">${p.after}</span></strong></div>
        </div>
      </section>`;
    }).join('');
    const eliminationAction=eliminated.length?` · Eliminated ${eliminated.map(p=>escapeHtml(p.targetName)).join(', ')}`:'';
    showModal('Confirm Player Activation',`
      <p>${escapeHtml(playerName(stage.playerOperativeId))} will be marked activated. NPO damage has not been applied yet.</p>
      ${eliminationBanner}
      <div class="summary-box"><strong>AP used:</strong> ${playerActionCost(stage)} / ${stage.apl}</div>
      ${attackRows||'<div class="summary-box"><strong>No attacks to apply.</strong></div>'}
      <div class="summary-box"><strong>Actions:</strong> ${escapeHtml(playerActivationSummary(stage))}${eliminationAction}</div>
      <div class="wizard-actions"><button class="btn ghost" id="backToPlayerActivation">Go Back</button><button class="btn primary" id="commitPlayerActivation">Confirm Activation</button></div>`);
    $('#backToPlayerActivation').onclick=()=>showPlayerActivation(stage);
    $('#commitPlayerActivation').onclick=()=>{
      if(applyPendingPlayerDamage(stage))return;
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
      log(`${playerName(stage.playerOperativeId)} ${pending.attackType==='shoot'?'shot':'made a Melee attack against'} ${npoName(n)} for ${pending.damage} damage (${before} → ${n.wounds} wounds).`);
      if(checkGameEnd())return true;
    }
    return false;
  }

  function completePlayerActivation(stage={}){
    let inc=0;
    if(stage.shoot)inc++;
    if(stage.melee)inc++;
    if(stage.damage)inc++;
    if(stage.hatch){
      const r=roll();
      if(r>=4)inc++;
    }
    if(stage.breach){
      inc++;
      const r=roll();
      if(r>=4)inc++;
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

  function npoName(n){
    if(!n)return 'NPO';
    const sameType=state.roster.filter(x=>x.type===n.type);
    if(sameType.length<=1)return n.type;
    const index=sameType.findIndex(x=>x.id===n.id);
    return `${n.type} ${index+1}`;
  }

  function sortOperativesGlobally(){
    const compareText=(a,b)=>String(a||'').localeCompare(String(b||''),undefined,{sensitivity:'base',numeric:true});

    // Sort the complete Player team definition so setup, selectors, and roster views agree.
    if(Array.isArray(playerTeamData?.operatives)){
      playerTeamData.operatives.sort((a,b)=>compareText(a.name,b.name)||compareText(a.id,b.id));
    }

    // Sort selected Player operatives by their roster names.
    if(Array.isArray(state.playerRoster)){
      state.playerRoster.sort((a,b)=>compareText(playerName(a),playerName(b))||compareText(a,b));
    }

    // Sort the authoritative NPO roster by type. The centralized npoName()
    // function then assigns duplicate numbers consistently everywhere.
    if(Array.isArray(state.roster)){
      state.roster.sort((a,b)=>compareText(a.type,b.type)||compareText(a.id,b.id));
    }
  }

  function playerAttackWeapons(operativeId,attackType){
    const operative=playerDefinition(operativeId);
    const wantedType=attackType==='shoot'?'ranged':'melee';
    return (operative?.weapons||[]).filter(w=>w.type===wantedType);
  }

  function parseWeaponDamage(damage){
    const match=String(damage||'0/0').match(/(\d+)\s*\/\s*(\d+)/);
    return {normal:Number(match?.[1]||0),crit:Number(match?.[2]||0)};
  }

  function weaponPiercingValue(weapon){
    for(const rule of weapon?.rules||[]){
      const match=String(rule).match(/(?:Piercing|AP)\s*(\d+)/i);
      if(match)return Number(match[1]);
    }
    return 0;
  }

  function playerWeaponProfile(weapon){
    const damage=parseWeaponDamage(weapon?.damage);
    return {
      dice:Number(weapon?.attacks||4),
      hit:Number(weapon?.hit||3),
      normal:damage.normal,
      crit:damage.crit,
      ap:weaponPiercingValue(weapon)
    };
  }

  function showPendingPlayerAttackWizard(stage,attackType,onResolved,onCancel,onSkip=null){
    const targets=activeNpos().filter(n=>projectedNpoWounds(n.id,stage)>0);
    if(!targets.length){
      showToast('No active NPO is available as a target.');
      showPlayerActivation(stage);
      return;
    }

    const attackLabel=attackType==='shoot'?'Shooting':'Melee';
    const weapons=playerAttackWeapons(stage.playerOperativeId,attackType);
    if(!weapons.length){
      showToast(`${playerName(stage.playerOperativeId)} has no ${attackType==='shoot'?'ranged':'melee'} weapon in its roster profile.`);
      showPlayerActivation(stage);
      return;
    }

    const weaponControl=weapons.length===1
      ? `<div class="field"><label>Weapon</label><div class="readonly-select" id="singleWeaponDisplay">${escapeHtml(weapons[0].name)}</div><input type="hidden" id="playerWeaponSelect" value="0"></div>`
      : `<div class="field"><label>Weapon</label><select id="playerWeaponSelect">${weapons.map((w,i)=>`<option value="${i}">${escapeHtml(w.name)}</option>`).join('')}</select></div>`;
    const singleTarget=targets.length===1?targets[0]:null;
    const targetControl=singleTarget
      ? `<div class="field"><label>Target NPO</label><div class="readonly-select">${escapeHtml(npoName(singleTarget))} · Wounds ${projectedNpoWounds(singleTarget.id,stage)}/${singleTarget.maxWounds} · Save ${singleTarget.save}+</div><input type="hidden" id="combatTarget" value="${singleTarget.id}"></div>`
      : `<div class="field"><label>Target NPO</label><select id="combatTarget"><option value="">Select a target NPO...</option>${targets.map(n=>`<option value="${n.id}">${escapeHtml(npoName(n))} · Wounds ${projectedNpoWounds(n.id,stage)}/${n.maxWounds} · Save ${n.save}+</option>`).join('')}</select></div>`;

    const priorElimination=attackType==='melee'&&Number(stage.pendingShoot?.after)<=0
      ? `<section class="compact-elimination-notice"><strong>☠ ${escapeHtml(stage.pendingShoot.targetName)} was eliminated by the Shoot attack.</strong><span>Choose another melee target or skip Melee.</span></section>`
      : '';
    showModal(`Resolve ${attackLabel} Attack`,`
      ${priorElimination}
      <p>Select the target NPO and weapon. This attack remains pending until the entire Player activation is confirmed.</p>
      ${targetControl}
      ${weaponControl}
      <fieldset id="combatControls" class="combat-fieldset"${singleTarget?'':' disabled'}>
        <section class="defense-profile attack-profile" aria-label="Player attack profile">
          <p class="eyebrow">PLAYER ATTACK PROFILE</p>
          <div class="defense-profile-grid" id="playerAttackProfile"></div>
        </section>
        <section class="defense-profile npo-defense-profile" aria-label="NPO defense profile">
          <p class="eyebrow">NPO DEFENSE PROFILE</p>
          <div class="defense-profile-grid">
            <div><small>NPO Defense Dice</small><strong>3</strong></div>
            <div><small>NPO Save</small><strong id="npoSaveValue">—</strong></div>
          </div>
          <label class="check-row compact-check defense-cover-row"><input type="checkbox" id="npoCover"><span><strong>NPO retains one normal save for cover</strong></span></label>
        </section>
        <div id="combatResults" class="combat-results"><p>${singleTarget?'Review the profiles, then roll the attack.':'Select a target NPO to begin.'}</p></div>
        <div class="wizard-actions"><button class="btn ghost" id="cancelPendingAttack">Cancel</button>${attackType==='melee'&&onSkip?'<button class="btn secondary" id="skipPendingMelee">Skip Melee</button>':''}<button class="btn primary" id="rollPendingAttack">Roll Attack & Saves</button></div>
      </fieldset>`);

    requestAnimationFrame(()=>{
      modal.scrollTop=0;
      modalBody.scrollTop=0;
      const inner=$('.modal-inner',modal);
      if(inner)inner.scrollIntoView({block:'start',behavior:'auto'});
    });

    const targetSelect=$('#combatTarget');
    const weaponSelect=$('#playerWeaponSelect');
    const controls=$('#combatControls');

    const renderProfile=()=>{
      const weapon=weapons[Number(weaponSelect?.value)||0];
      const profile=playerWeaponProfile(weapon);
      const target=state.roster.find(x=>x.id===targetSelect.value);
      $('#playerAttackProfile').innerHTML=`
        <div><small>Attack Dice</small><strong>${profile.dice}</strong></div>
        <div><small>Hit On</small><strong>${profile.hit}+</strong></div>
        <div><small>Normal Damage</small><strong>${profile.normal}</strong></div>
        <div><small>Critical Damage</small><strong>${profile.crit}</strong></div>
        <div><small>AP</small><strong>${profile.ap}</strong></div>`;
      const saveValue=$('#npoSaveValue');
      if(saveValue)saveValue.textContent=target?`${target.save}+`:'—';
    };

    targetSelect.addEventListener('change',()=>{
      controls.disabled=!targetSelect.value;
      renderProfile();
      if(targetSelect.value)$('#combatResults').innerHTML='<p>Review the profiles, then roll the attack.</p>';
    });
    weaponSelect?.addEventListener('change',()=>{
      renderProfile();
      $('#combatResults').innerHTML=targetSelect.value?'<p>Review the profiles, then roll the attack.</p>':'<p>Select a target NPO to begin.</p>';
    });

    renderProfile();
    $('#cancelPendingAttack').onclick=onCancel;
    if($('#skipPendingMelee'))$('#skipPendingMelee').onclick=onSkip;
    $('#rollPendingAttack').onclick=()=>previewPendingPlayerAttack(stage,attackType,onResolved,onCancel);
  }

  function previewPendingPlayerAttack(stage,attackType,onResolved,onCancel){
    const n=state.roster.find(x=>x.id===$('#combatTarget').value);
    if(!n)return;
    const weapons=playerAttackWeapons(stage.playerOperativeId,attackType);
    const weapon=weapons[Number($('#playerWeaponSelect')?.value)||0];
    const profile=playerWeaponProfile(weapon);
    const attackDice=rollAttack(profile);
    const defense=resolveDefense(attackDice,3,n.save,profile.ap,$('#npoCover').checked,profile);
    const before=projectedNpoWounds(n.id,stage);
    const after=Math.max(0,before-defense.damage);
    const result={attackType,targetId:n.id,targetName:npoName(n),weaponName:weapon.name,before,after,damage:defense.damage};

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

  const npoQuestionIcons = {
    engaged:'blades',charge:'route',shot:'crosshair',objective:'objective',
    wounded:'wounded',hatch:'hatch',cover:'shield',clustered:'group'
  };

  function npoIcon(type){
    const paths={
      blades:'<path d="M7 4l13 13M17 4l3 3L7 20l-3-3L17 4zM5 19l-2 2m16-2l2 2"/>',
      route:'<path d="M4 18c4-8 8-1 13-9"/><path d="M13 6h5v5"/><circle cx="5" cy="18" r="2"/>',
      crosshair:'<circle cx="12" cy="12" r="7"/><circle cx="12" cy="12" r="2"/><path d="M12 2v4m0 12v4M2 12h4m12 0h4"/>',
      objective:'<path d="M6 21V4m0 1h11l-2 4 2 4H6"/><circle cx="6" cy="21" r="2"/>',
      wounded:'<path d="M12 21s-7-4.4-7-10a4 4 0 017-2.7A4 4 0 0119 11c0 5.6-7 10-7 10z"/><path d="M9 12h2l1-3 2 6 1-3h2"/>',
      hatch:'<path d="M5 21V3h14v18M8 21V6h8v15"/><circle cx="14" cy="13" r=".8"/><path d="M3 21h18"/>',
      shield:'<path d="M12 3l7 3v5c0 5-3 8-7 10-4-2-7-5-7-10V6l7-3z"/><path d="M8 12h8"/>',
      group:'<circle cx="9" cy="8" r="3"/><circle cx="17" cy="10" r="2.5"/><path d="M3 20c0-4 2-6 6-6s6 2 6 6m0-5c3 0 5 2 5 5"/>',
      command:'<path d="M12 2l3 6 6 1-4.5 4.5 1 6.5-5.5-3-5.5 3 1-6.5L3 9l6-1 3-6z"/><circle cx="12" cy="12" r="2"/>'
    };
    return `<svg class="npo-question-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${paths[type]||paths.command}</svg>`;
  }

  function renderCompletedNpoQuestions(history){
    return history.map(item=>{const q=npoQuestions.find(question=>question.key===item.key);return q?`<div class="npo-question-complete">${npoIcon(npoQuestionIcons[q.key])}<span>${escapeHtml(q.title)}</span><strong>${item.answer?'Yes':'No'}</strong></div>`:'';}).join('');
  }

  function renderActiveNpoQuestion(q){
    return `<section class="npo-question-active" aria-live="polite" aria-atomic="true">
      ${npoIcon(npoQuestionIcons[q.key])}<h3>${escapeHtml(q.title)}</h3><p>${escapeHtml(q.help)}</p>
      <div class="ai-choice-grid"><button class="ai-choice no" data-answer="no"><strong>No</strong></button><button class="ai-choice yes" data-answer="yes"><strong>Yes</strong></button></div>
    </section>`;
  }

  function showNpoWizard(){
    const n=nextNpo(); if(!n)return;
    runNpoPrompt(n,'engaged',{},[]);
  }

  function nextNpoQuestionKey(n,key,answers){
    if(key==='engaged')return answers.engaged?'objective':'objective';
    if(key==='objective')return answers.objective?'charge':'wounded';
    if(key==='wounded')return answers.wounded?'charge':'clustered';
    if(key==='clustered')return 'charge';
    if(key==='charge'){
      const decisiveCharge=answers.charge&&(n.behavior==='Brawler'||n.behavior==='Guardian'||answers.objective||answers.wounded);
      if(answers.engaged||decisiveCharge)return null;
      return 'shot';
    }
    if(key==='shot')return answers.shot?'cover':'hatch';
    if(key==='hatch')return answers.hatch?null:'cover';
    if(key==='cover')return null;
    return null;
  }

  function runNpoPrompt(n,key,answers,history){
    const q=npoQuestions.find(item=>item.key===key);
    if(!q){resolveNpo(n,answers,history);return;}
    const priorTop=$('.npo-question-active',modal)?.getBoundingClientRect().top;
    modalBody.innerHTML=`<div class="modal-inner"><h2>NPO Activation: ${escapeHtml(npoName(n))}</h2><div class="ai-wizard">
      <div class="npo-question-flow">${renderCompletedNpoQuestions(history)}${renderActiveNpoQuestion(q)}</div>
      <div class="wizard-actions">
        <button class="btn ghost" data-close>Exit Guide</button>
        <button class="btn ghost" id="aiBack" ${history.length===0?'disabled':''}>Back</button>
      </div>
    </div></div>`;
    if(!modal.open)modal.showModal();
    $('[data-close]',modal).onclick=closeModal;
    if(priorTop!==undefined)requestAnimationFrame(()=>{const active=$('.npo-question-active',modal);if(!active)return;const delta=active.getBoundingClientRect().top-priorTop;modal.scrollBy({top:delta,behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth'});});
    $$('[data-answer]',modal).forEach(btn=>btn.onclick=()=>{
      const answer=btn.dataset.answer==='yes';
      const nextAnswers={...answers,[q.key]:answer};
      const nextKey=nextNpoQuestionKey(n,key,nextAnswers);
      const nextHistory=[...history,{key,answers,answer}];
      if(nextKey)runNpoPrompt(n,nextKey,nextAnswers,nextHistory);
      else resolveNpo(n,nextAnswers,nextHistory);
    });
    $('#aiBack')?.addEventListener('click',()=>{
      const previous=history[history.length-1];
      if(previous)runNpoPrompt(n,previous.key,previous.answers,history.slice(0,-1));
    });
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

  function resolveNpo(n,c,questionHistory=[]){
    state.npoAttackTargetId=null;
    const decision=chooseNpoDecision(n,c);
    const attacks=decision.action.includes('Fight')||decision.action.includes('Shoot');
    const dice=[];
    if(decision.threat)setThreat(decision.threat,`${npoName(n)} ${decision.action.includes('Fight')?'Fight':'Shoot'}`);
    n.ready=false;state.npoActivated++;state.activationNumber++;
    state.activationHistory.unshift({side:'npo',label:npoName(n),action:decision.action,target:null});
    state.activeNpoId=null;advanceAfterActivation('npo');
    state.lastActivation={name:npoName(n),...decision,dice,answers:c,questionHistory,attackRequired:attacks,targetConfirmed:false};
    log(`${npoName(n)}: ${decision.action}.`);save();

    renderNpoDecisionResult(n,decision,dice,c,false,false,attacks,false,questionHistory);
  }

  function initiativeSummary(dice){
    const crits=dice.filter(d=>d.kind==='crit').length;
    const hits=dice.filter(d=>d.kind==='hit').length;
    const misses=dice.filter(d=>d.kind==='miss').length;
    if(crits===0&&hits===0)return 'Attack missed. No saves or damage required.';
    return `${crits} critical · ${hits} normal · ${misses} miss`;
  }

  function renderNpoDecisionResult(n,decision,dice,answers,attackResolved,animateDice=true,attackRequired=(decision.action.includes('Fight')||decision.action.includes('Shoot')),targetConfirmed=dice.length>0,questionHistory=state.lastActivation?.questionHistory||[]){
    const eligibleTargetIds=eligibleNpoAttackTargets();
    if(!targetConfirmed&&eligibleTargetIds.length===1)state.npoAttackTargetId=eligibleTargetIds[0];
    state.lastActivation={name:npoName(n),...decision,dice,answers,questionHistory,attackResolved,attackRequired,targetConfirmed};save();
    const targetOptions=eligibleTargetIds.map(id=>`<option value="${escapeHtml(id)}" ${state.npoAttackTargetId===id?'selected':''}>${escapeHtml(playerName(id))}</option>`).join('');
    const targetName=state.npoAttackTargetId?playerName(state.npoAttackTargetId):'';
    const targetField=targetConfirmed||eligibleTargetIds.length===1
      ? `<input id="npoPriorityTarget" value="${escapeHtml(targetName)}" readonly>`
      : `<select id="npoPriorityTarget" ${attackResolved?'disabled':''}><option value="">Select matching operative</option>${targetOptions}</select>`;
    modalBody.innerHTML=`<div class="modal-inner ai-result">
      <div class="npo-question-flow">${renderCompletedNpoQuestions(questionHistory)}</div>
      <div class="ai-result-title"><div><h2>${escapeHtml(npoName(n))}</h2><p>${escapeHtml(n.type)} · ${escapeHtml(n.behavior)}</p></div></div>
      <div class="npo-result-card">${npoIcon('command')}<div><small>ACTIVATION PLAN</small><strong>${escapeHtml(decision.action)}</strong><p>${escapeHtml(decision.reason)}</p><div class="npo-target-priority"><small>TARGET PRIORITY</small><strong>${escapeHtml(decision.target)}</strong>${attackRequired?`<div class="field target-selection"><label for="npoPriorityTarget">Target Player Operative</label>${targetField}</div>`:''}</div></div></div>
      ${attackRequired&&!targetConfirmed?`<button class="btn secondary big-action" id="confirmNpoTarget" ${state.npoAttackTargetId?'':'disabled'}>Confirm Target</button>`:''}
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
      <div class="wizard-actions"><button class="btn primary" id="completeNpo" ${attackRequired&&!attackResolved?'disabled':''}>Complete Activation</button></div>
    </div>`;
    if(!modal.open)modal.showModal();
    if(attackRequired&&targetConfirmed&&!attackResolved&&animateDice){setTimeout(()=>{const box=$('#aiDice');if(!box)return;box.innerHTML=dice.map(dieHtml).join('');box.classList.add('settled');$('#aiDiceSummary').textContent=initiativeSummary(dice);},850);}
    $('#npoPriorityTarget')?.addEventListener('change',()=>{state.npoAttackTargetId=$('#npoPriorityTarget').value||null;const b=$('#confirmNpoTarget');if(b)b.disabled=!state.npoAttackTargetId;save();});
    $('#confirmNpoTarget')?.addEventListener('click',()=>{
      if(!state.npoAttackTargetId)return;
      state.npoAttackSummary=null;
      const rolledDice=rollAttack(n.attack);
      const history=state.activationHistory.find(x=>x.side==='npo'&&x.label===npoName(n)&&!x.target);
      if(history)history.target=playerName(state.npoAttackTargetId);
      log(`${npoName(n)} confirmed ${playerName(state.npoAttackTargetId)} as the attack target and rolled the attack dice.`);
      save();
      showNpoAttackWizard(n,rolledDice,(summary)=>{
        state.npoAttackSummary=summary;
        save();
        renderNpoDecisionResult(n,decision,rolledDice,answers,true,false,true,true);
      },()=>{
        state.npoAttackTargetId=null;
        state.npoAttackSummary=null;
        save();
        renderNpoDecisionResult(n,decision,[],answers,false,false,true,false);
      },true);
    });

    $('#completeNpo').onclick=()=>{state.npoAttackTargetId=null;state.npoAttackSummary=null;save();closeModal();render();};
  }

  function showNpoAttackWizard(n,attackDice,onDone,onCancel,animateAttackDice=false){
    const target=selectedNpoAttackTarget();
    if(!target){showToast('Select the targeted Player operative first.');if(onCancel)onCancel();return;}
    showModal('NPO Attack Wizard',`<p>${escapeHtml(npoName(n))} is attacking <strong>${escapeHtml(target.name)}</strong>.</p>
      <div class="combat-stage"><small>NPO ATTACK DICE</small><div class="dice-row ${animateAttackDice?'animated-roll':'settled'}" id="npoAttackDiceResult">${animateAttackDice?attackDice.map(()=>rollingDieHtml()).join(''):attackDice.map(dieHtml).join('')}</div><p id="npoAttackDiceSummary">${animateAttackDice?`Rolling ${attackDice.length} attack dice…`:initiativeSummary(attackDice)}</p><p>${n.attack.normal}/${n.attack.crit} damage · Hit ${n.attack.hit}+</p></div>
      <div class="combat-stage target-summary"><small>TARGET PLAYER OPERATIVE</small><strong>${escapeHtml(target.name)}</strong><p>${escapeHtml(target.type||target.role||'Player Operative')}</p></div>
      <section class="defense-profile" aria-label="Player defense profile">
        <p class="eyebrow">PLAYER DEFENSE PROFILE</p>
        <div class="defense-profile-grid">
          <div><small>Defense Dice</small><strong>3</strong></div>
          <div><small>Save</small><strong>${target.save||3}+</strong></div>
          <div><small>NPO AP</small><strong>${n.attack.ap||0}</strong></div>
          <div><small>Current Wounds</small><strong>${target.wounds||10}</strong></div>
        </div>
      </section>
      <label class="check-row compact-check"><input type="checkbox" id="playerCover"><span><strong>Player retains one normal save for cover</strong></span></label>
      <div id="combatResults" class="combat-results"></div>
      <div class="wizard-actions"><button class="btn ghost" id="cancelNpoAttack">Cancel</button><button class="btn primary" id="rollNpoSaves">Roll Player Saves</button></div>`);
    const rollSavesButton=$('#rollNpoSaves');
    if(animateAttackDice){
      rollSavesButton.disabled=true;
      setTimeout(()=>{
        const diceBox=$('#npoAttackDiceResult');
        if(diceBox){
          diceBox.innerHTML=attackDice.map(dieHtml).join('');
          diceBox.classList.remove('animated-roll');
          diceBox.classList.add('settled');
        }
        const summary=$('#npoAttackDiceSummary');
        if(summary)summary.textContent=initiativeSummary(attackDice);
        rollSavesButton.disabled=false;
      },850);
    }
    $('#cancelNpoAttack').onclick=()=>{save();if(onCancel)onCancel();};
    $('#rollNpoSaves').onclick=()=>{
      const defenseDice=3;
      const saveTarget=target.save||3;
      const npoAp=n.attack.ap||0;
      const before=target.wounds||10;
      const result=resolveDefense(attackDice,defenseDice,saveTarget,npoAp,$('#playerCover').checked,n.attack);
      const after=Math.max(0,before-result.damage);
      $('#combatResults').innerHTML=`<div class="combat-stage"><small>PLAYER SAVE DICE</small><div class="dice-row animated-roll" id="playerSaveDiceResult">${result.saveDice.map(()=>rollingDieHtml()).join('')||'<span class="muted">No save dice rolled</span>'}</div>${result.coverRetained?'<span class="cover-retain">+ 1 retained normal cover save</span>':''}</div><div class="damage-summary"><div><small>Target</small><strong>${escapeHtml(target.name)}</strong></div><div><small>Unsaved normal hits</small><strong>${result.normalRemaining}</strong></div><div><small>Unsaved critical hits</small><strong>${result.critRemaining}</strong></div><div><small>Damage</small><strong>${result.damage}</strong></div><div><small>Player wounds</small><strong>${before} → ${after}</strong></div></div><p class="muted">Apply this wound change to ${escapeHtml(target.name)} on the tabletop.</p>`;
      $('#playerCover').disabled=true;
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
        state.playerWounds=state.playerWounds||{};
        state.playerWounds[target.id]=after;
        const casualties=new Set(state.playerCasualtyIds||[]);
        if(after<=0){
          casualties.add(target.id);
          if(!state.playerActivatedIds.includes(target.id))state.playerActivatedIds.push(target.id);
        }else{
          casualties.delete(target.id);
        }
        state.playerCasualtyIds=[...casualties];
        state.playerReady=playerOperativesRemaining();
        log(`${npoName(n)} dealt ${result.damage} damage to ${target.name} (${before} → ${after} wounds).`);
        if(checkGameEnd())return;
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
  function renderRoster(){app.innerHTML=`<div class="panel-title"><div><p class="eyebrow">NPO ROSTER</p><h2>${activeNpos().length} active NPOs</h2><p>Wounds and Ready status update the guided activation flow.</p></div><button class="btn secondary" id="addNpo">Add NPO</button></div><div class="player-roster-grid npo-roster-grid">${state.roster.length?state.roster.map(n=>npoRosterCard(n,true)).join(''):'<div class="card empty">No NPOs are currently on the battlefield.</div>'}</div>`;$('#addNpo').onclick=showAddNpo;$$('[data-player-attack]').forEach(b=>b.onclick=()=>showPlayerAttackWizard(b.dataset.playerAttack));$$('[data-wound]').forEach(b=>b.onclick=()=>adjustWounds(b.dataset.wound,-1));$$('[data-heal]').forEach(b=>b.onclick=()=>adjustWounds(b.dataset.heal,1));$$('[data-ready]').forEach(b=>b.onclick=()=>toggleReady(b.dataset.ready));$$('[data-delete]').forEach(b=>b.onclick=()=>deleteNpo(b.dataset.delete));}
  function renderPlayerRoster(){
    const casualties=new Set(state.playerCasualtyIds||[]);
    const activated=new Set(state.playerActivatedIds||[]);
    const cards=(state.playerRoster||[]).map(id=>{
      const operative=livePlayerOperative(id);
      if(!operative)return '';
      const eliminated=casualties.has(id);
      const status=eliminated?'ELIMINATED':activated.has(id)?'ACTIVATED':'READY';
      const weaponNames=(operative.weapons||[]).map(w=>escapeHtml(w.name)).join(' · ');
      return `<article class="operative-card ${eliminated?'dead':''}"><div class="player-roster-card-heading"><div><h4>${escapeHtml(operative.name)}</h4><p>${escapeHtml(operative.role||'Operative')}</p></div><strong>${status}</strong></div><div class="stat-grid compact-stats"><div class="stat"><small>APL</small><strong>${operative.apl??'—'}</strong></div><div class="stat"><small>MOVE</small><strong>${operative.move??'—'}"</strong></div><div class="stat"><small>SAVE</small><strong>${operative.save??'—'}+</strong></div><div class="stat"><small>WOUNDS</small><strong>${playerCurrentWounds(id)}/${playerDefinition(id)?.wounds??operative.wounds}</strong></div></div>${weaponNames?`<p class="player-roster-weapons"><strong>Weapons:</strong> ${weaponNames}</p>`:''}<button class="btn ${eliminated?'secondary':'ghost'}" data-player-roster-status="${id}">${eliminated?'Restore Operative':'Update Status'}</button></article>`;
    }).join('');
    const teamName=playerTeamData?.teamName||playerTeamEntry()?.name||'Player';
    app.innerHTML=`<div class="panel-title"><div><p class="eyebrow">PLAYER ROSTER</p><h2>${escapeHtml(teamName)}</h2><p>${livingPlayerOperativeCount()} active of ${(state.playerRoster||[]).length} selected operatives.</p></div></div><div class="roster-grid">${cards||'<div class="card empty">No Player operatives were selected for this game.</div>'}</div>`;
    $$('[data-player-roster-status]').forEach(button=>button.onclick=()=>showPlayerOperativeStatus(button.dataset.playerRosterStatus));
  }
  function npoRosterCard(n,controls){
    const status=n.wounds<=0?'ELIMINATED':n.ready?'READY':'ACTIVATED';
    return `<article class="player-roster-card npo-roster-card ${n.wounds<=0?'dead':''}">
      <div class="player-roster-card-head"><div><strong>${escapeHtml(npoName(n))}</strong><small>${escapeHtml(n.behavior)}</small></div><span class="npo-status-badge ${status.toLowerCase()}">${status}</span></div>
      <div class="operative-stat-line"><span><small>ATTACK</small><b>${n.attack?.dice??'—'}</b></span><span><small>HIT</small><b>${n.attack?.hit??'—'}+</b></span><span><small>SAVE</small><b>${n.save}+</b></span><span><small>WOUNDS</small><b>${n.wounds}/${n.maxWounds}</b></span></div>
      ${controls?`<div class="quick-actions"><button class="btn secondary" data-player-attack="${n.id}">Player Attack</button><button class="btn ghost" data-wound="${n.id}">− Wound</button><button class="btn ghost" data-heal="${n.id}">+ Heal</button><button class="btn secondary" data-ready="${n.id}">${n.ready?'Expend':'Ready'}</button><button class="btn danger" data-delete="${n.id}">Delete</button></div>`:''}
    </article>`;
  }
  function operativeCard(n,controls){return npoRosterCard(n,controls);}
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
  function showAddNpo(){showModal('Add NPO',`<div class="field"><label>NPO type</label><select id="newNpoType">${Object.keys(profiles).map(x=>`<option>${x}</option>`).join('')}</select></div><div class="wizard-actions"><button class="btn ghost" data-close>Cancel</button><button class="btn primary" id="confirmAdd">Add NPO</button></div>`);$('#confirmAdd').onclick=()=>{if(activeNpos().length>=MAX_NPOS){showToast(`Only ${MAX_NPOS} active NPOs can be on the battlefield.`);return;}const type=$('#newNpoType').value,p=profiles[type];state.roster.push({id:uid(),name:`${type} ${state.roster.length+1}`,type,behavior:p.behavior,maxWounds:p.wounds,wounds:p.wounds,save:p.save,attack:{...p.attack},ready:true,deployed:true});log(`${type} added to the battlefield.`);closeModal();save();render();};}
  function adjustWounds(id,d){const n=state.roster.find(x=>x.id===id);if(!n)return;n.wounds=Math.max(0,Math.min(n.maxWounds,n.wounds+d));if(n.wounds===0)n.ready=false;if(checkGameEnd())return;save();render();}
  function toggleReady(id){const n=state.roster.find(x=>x.id===id);if(n&&n.wounds>0)n.ready=!n.ready;save();render();}
  function deleteNpo(id){state.roster=state.roster.filter(x=>x.id!==id);save();render();}

  function showModal(title,content,onClose){
    const active=document.activeElement;
    if(active&&typeof active.blur==='function')active.blur();

    modalBody.innerHTML=`<div class="modal-inner"><h2>${title}</h2>${content}</div>`;
    modal.setAttribute('tabindex','-1');
    if(!modal.open)modal.showModal();
    modal._onClose=onClose;
    $$('[data-close]',modal).forEach(b=>b.onclick=closeModal);

    requestAnimationFrame(()=>{
      modal.scrollTop=0;
      modalBody.scrollTop=0;
      try{modal.focus({preventScroll:true});}catch{modal.focus();}
    });
  }
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
        <button class="btn secondary" data-game-view="player-roster">Player Roster</button>
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

  function confirmNewGame(){showModal('Start New Game?',`<p>This will replace the current mission, roster, Threat, Turning Point, and Journal.</p><div class="wizard-actions"><button class="btn ghost" data-close>Cancel</button><button class="btn danger" id="confirmNewGame">Start New Game</button></div>`);$('#confirmNewGame').onclick=()=>{localStorage.removeItem(STORAGE_KEY);state=initialState();state.screen='setup';expandedRosterCategories=null;closeModal();save();render();};}
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

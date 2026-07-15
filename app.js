(() => {
  'use strict';

  const STORAGE_KEY = 'tombWorldSoloGuide.v1';
  const APP_VERSION = '1.3.2';
  const MAX_NPOS = 10;
  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => [...root.querySelectorAll(sel)];
  const app = $('#app');
  const nav = $('#bottomNav');
  const modal = $('#modal');
  const modalBody = $('#modalBody');
  const toast = $('#toast');
  const importInput = $('#importInput');

  const missions = [
    {id:'shifting-labyrinth',number:'01',name:'Shifting Labyrinth',brief:'Escape a tomb complex while its route shifts around the kill team.',objective:'Get at least half of your surviving Enemy operatives through the escape point.',setup:'2D3 + 3',tracker:'Operatives escaped',max:12,orientation:'left',special:'The escape point may move during the mission.'},
    {id:'demolition-protocol',number:'02',name:'Demolition Protocol',brief:'Open a route by operating hatchways and breaching sealed access points.',objective:'Open and breach seven access points before the Enemy kill team is eliminated.',setup:'2D3 + 3',tracker:'Access points breached',max:7,orientation:'left',special:'Operate Hatch and Breach can increase Threat.'},
    {id:'recover-transponder',number:'03',name:'Recover Transponder',brief:'Search several locations for a hidden device and carry it back to safety.',objective:'Find the true transponder and escape through the Enemy board edge.',setup:'2D3 + 3',tracker:'Search sites resolved',max:3,orientation:'bottom',special:'Only one objective is the true transponder.'},
    {id:'destroy-sarcophagus',number:'04',name:'Destroy Sarcophagus',brief:'Overload a damaged stasis crypt while tomb systems attempt to repair it.',objective:'Accumulate 20 destruction points before the Enemy team is eliminated.',setup:'D3 + 6',tracker:'Destruction points',max:20,orientation:'bottom',special:'The sarcophagus may repair itself during strategy resolution.'},
    {id:'scout-sub-crypt',number:'05',name:'Scout Sub-Crypt',brief:'Explore sealed rooms and clear the guardians that awaken inside.',objective:'Scout three eligible rooms after clearing each room of active NPOs.',setup:'0',tracker:'Rooms scouted',max:3,orientation:'bottom',special:'No NPOs start on the board. Rooms awaken NPOs when opened or entered.'},
    {id:'regroup',number:'06',name:'Regroup',brief:'Navigate unstable phasing routes and reunite the scattered Enemy team.',objective:'Finish a Turning Point with every surviving Enemy operative in the regroup zone.',setup:'2D3 + 3',tracker:'Operatives regrouped',max:12,orientation:'left',special:'Hatchway access points may relocate operatives.'}
  ];

  const profiles = {
    'Necron Warrior': {behavior:'Marksman',wounds:10,save:3,attack:{dice:4,hit:4,normal:3,crit:4}},
    'Canoptek Scarab Swarm': {behavior:'Brawler',wounds:8,save:4,attack:{dice:5,hit:4,normal:2,crit:3}},
    'Canoptek Macrocyte': {behavior:'Sentinel',wounds:9,save:4,attack:{dice:4,hit:3,normal:3,crit:4}},
    'Canoptek Tomb Crawler': {behavior:'Guardian',wounds:12,save:3,attack:{dice:4,hit:3,normal:4,crit:5}}
  };

  const maps = {
    'shifting-labyrinth': {walls:[[180,30,180,155],[270,155,270,300],[430,30,430,160],[610,150,610,300],[680,300,680,460],[180,155,610,155],[270,300,680,300],[430,390,610,390]],hatches:[[270,215,'v'],[430,95,'v'],[430,350,'v'],[520,155,'h'],[560,300,'h'],[610,225,'v']],markers:[[770,245,'ESCAPE']]},
    'demolition-protocol': {walls:[[350,30,350,175],[500,30,500,185],[140,175,650,175],[250,175,250,325],[450,175,450,460],[650,175,650,325],[150,325,650,325]],hatches:[[350,100,'v'],[500,110,'v'],[250,245,'v'],[450,245,'v'],[650,245,'v'],[300,175,'h'],[550,175,'h'],[340,325,'h'],[555,325,'h']],markers:[[300,175,'BREACH'],[555,325,'BREACH']]},
    'recover-transponder': {walls:[[30,110,770,110],[250,110,250,265],[520,110,520,365],[30,265,520,265],[250,365,770,365]],hatches:[[250,185,'v'],[520,190,'v'],[520,320,'v'],[150,265,'h'],[385,265,'h'],[650,365,'h']],markers:[[165,205,'1'],[440,185,'2'],[625,320,'3']]},
    'destroy-sarcophagus': {walls:[[350,30,350,305],[530,120,530,365],[350,120,770,120],[30,305,530,305],[150,305,150,460],[150,395,530,395]],hatches:[[350,185,'v'],[530,185,'v'],[530,340,'v'],[245,305,'h'],[440,305,'h'],[330,395,'h']],markers:[[435,215,'SARCOPHAGUS']]},
    'scout-sub-crypt': {walls:[[160,30,160,235],[360,30,360,335],[590,100,590,335],[30,165,360,165],[360,255,770,255],[150,345,590,345]],hatches:[[160,105,'v'],[360,100,'v'],[360,285,'v'],[590,180,'v'],[250,165,'h'],[480,255,'h'],[300,345,'h']],markers:[[95,95,'1'],[260,95,'2'],[475,175,'3'],[680,165,'4'],[480,390,'5']]},
    'regroup': {walls:[[200,30,200,250],[390,30,390,460],[520,30,520,205],[200,135,650,135],[30,285,520,285],[200,395,770,395]],hatches:[[200,100,'v'],[390,90,'v'],[390,225,'v'],[520,115,'v'],[285,285,'h'],[455,285,'h'],[300,395,'h'],[620,395,'h']],markers:[[690,235,'REGROUP']]}
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
    version:'1.3.2', screen:'home', tab:'play', setupStep:0, missionId:null,
    setupChecks:[], roster:[], enemyCount:6, enemyReady:6, turningPoint:0,
    threat:0, initiative:'enemy', phase:'setup', nextSide:'enemy', tracker:0,
    activeNpoId:null, journal:[], lastActivation:null, newIds:[], completed:false,
    strategyStage:null, strategyData:null, activationNumber:0, enemyActivated:0, npoActivated:0,
    activationHistory:[], reinforcementEntry:'Nearest valid entry point'
  });

  let state = normalizeState(load() || initialState());

  function save(){ state.version=APP_VERSION; localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); }
  function load(){ try{return JSON.parse(localStorage.getItem(STORAGE_KEY));}catch{return null;} }
  function normalizeState(raw){
    const base=initialState(), merged={...base,...raw};
    merged.roster=Array.isArray(raw?.roster)?raw.roster:[];
    merged.journal=Array.isArray(raw?.journal)?raw.journal:[];
    merged.newIds=Array.isArray(raw?.newIds)?raw.newIds:[];
    merged.activationHistory=Array.isArray(raw?.activationHistory)?raw.activationHistory:[];
    return merged;
  }
  function mission(){ return missions.find(m => m.id === state.missionId) || missions[0]; }
  function roll(sides=6){ return Math.floor(Math.random()*sides)+1; }
  function rollD3(){ return roll(3); }
  function uid(){ return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2,7)}`; }
  function activeNpos(){ return state.roster.filter(n => n.wounds > 0); }
  function readyNpos(){ return activeNpos().filter(n => n.ready); }
  function threatGrade(){ return state.threat === 0 ? 0 : state.threat <= 5 ? 1 : state.threat <= 10 ? 2 : 3; }
  function threatLabel(){ return ['Dormant','Alert','Awakened','Full Awakening'][threatGrade()]; }
  function threatToNext(){ const g=threatGrade(); if(g===3)return 0; return [1,6,11][g]-state.threat; }
  function log(text){ state.journal.unshift({time:new Date().toISOString(),text}); state.journal=state.journal.slice(0,150); }
  function setThreat(amount,reason){ const before=state.threat; state.threat=Math.max(0,Math.min(15,state.threat+amount)); if(state.threat!==before) log(`Threat ${before} → ${state.threat}: ${reason}`); }
  function escapeHtml(s){ return String(s).replace(/[&<>'"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[c])); }

  function generateRoster(){
    const m=mission(); let count=0, formula='0';
    if(m.setup==='2D3 + 3'){ const a=rollD3(),b=rollD3(); count=a+b+3; formula=`${a} + ${b} + 3 = ${count}`; }
    if(m.setup==='D3 + 6'){ const a=rollD3(); count=a+6; formula=`${a} + 6 = ${count}`; }
    const table=['Canoptek Scarab Swarm','Canoptek Scarab Swarm','Canoptek Macrocyte','Necron Warrior','Necron Warrior','Necron Warrior','Necron Warrior','Necron Warrior','Canoptek Tomb Crawler','Canoptek Tomb Crawler','Necron Warrior'];
    state.roster=[];
    for(let i=0;i<count;i++){
      const type=table[Math.min(table.length-1,Math.max(0,roll(6)+roll(6)-2))];
      const p=profiles[type]; state.roster.push({id:uid(),name:`${type} ${i+1}`,type,behavior:p.behavior,maxWounds:p.wounds,wounds:p.wounds,save:p.save,attack:{...p.attack},ready:false,deployed:false});
    }
    state.newIds=[]; log(`${m.name}: generated ${count} starting NPOs (${formula}).`); return {count,formula};
  }

  function render(){
    nav.hidden = state.screen !== 'game';
    if(state.screen==='home') renderHome();
    else if(state.screen==='setup') renderSetup();
    else renderGame();
    bindCommon();
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
    $('#homeHelpBtn').onclick=()=>showModal('How Tomb World Solo Guide Works',`<p>The Guide presents one required action at a time. A new game walks through mission choice, board setup, roster generation, and deployment. During play it alternates Enemy and NPO activations, tracks Threat, generates reinforcements, and records the battle.</p><div class="wizard-actions"><button class="btn primary" data-close>Understood</button></div>`);
  }

  const setupTitles=['Choose Mission','Build the Killzone','Generate NPO Roster','Deploy NPOs','Deploy Enemy Kill Team','Ready to Begin'];
  function renderSetup(){
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
    if(step===1){const m=mission();const checks=['Place walls and hatchways as shown','Place mission objective markers','Identify the Enemy drop zone','Identify NPO deployment areas'];return `<h3>${m.name} board setup</h3><p><strong>Objective:</strong> ${m.objective}</p>${boardSvg(m.id)}<div class="checklist">${checks.map((c,i)=>`<label class="check-row"><input type="checkbox" data-check="${i}" ${state.setupChecks[i]?'checked':''}><span><strong>${c}</strong><small>${i===0?'Use the official mission map shown above to place the terrain and markers.':'Confirm this step on the physical board.'}</small></span></label>`).join('')}</div><div class="wizard-actions"><button class="btn ghost" id="setupBack">Back</button><button class="btn primary" id="setupNext" ${checks.every((_,i)=>state.setupChecks[i])?'':'disabled'}>Board Ready</button></div>`;}
    if(step===2){const m=mission();return `<h3>Mission starting roster</h3><p>${m.name} begins with <strong>${m.setup}</strong> NPOs.</p>${state.roster.length?`<div class="summary-box"><strong>${state.roster.length} NPOs generated</strong><br>${rosterBreakdown()}</div><div class="roster-preview">${state.roster.map(n=>operativeCard(n,false)).join('')}</div>`:`<div class="empty">No roster generated yet.</div>`}<div class="wizard-actions"><button class="btn ghost" id="setupBack">Back</button><button class="btn secondary" id="generateBtn">${state.roster.length?'Regenerate':'Generate'} Roster</button><button class="btn primary" id="setupNext" ${state.roster.length||m.setup==='0'?'':'disabled'}>Continue</button></div>`;}
    if(step===3){return `<h3>Deploy the NPOs</h3><p>${mission().setup==='0'?'This mission starts with no deployed NPOs. The Guide will add them as rooms awaken.':'Place each NPO on the physical board, then mark it deployed.'}</p><div class="deployment-list">${state.roster.length?state.roster.map(n=>`<div class="deployment-item ${n.deployed?'done':''}"><span><strong>${escapeHtml(n.name)}</strong><small>${n.behavior}</small></span><button class="btn ${n.deployed?'ghost':'secondary'}" data-deploy="${n.id}">${n.deployed?'Placed':'Mark Placed'}</button></div>`).join(''):'<div class="summary-box"><strong>No starting NPO deployment required.</strong></div>'}</div><div class="wizard-actions"><button class="btn ghost" id="setupBack">Back</button><button class="btn primary" id="setupNext" ${state.roster.every(n=>n.deployed)?'':'disabled'}>NPOs Deployed</button></div>`;}
    if(step===4) return `<h3>Deploy your Enemy kill team</h3><p>In the Guide, your solo player-controlled operatives are called <strong>Enemy operatives</strong> because all tactical prompts are written from the NPO’s perspective.</p><div class="field"><label for="enemyCount">Number of Enemy operatives</label><input id="enemyCount" type="number" min="1" max="20" value="${state.enemyCount}"></div><div class="checklist"><label class="check-row"><input id="enemyDeployed" type="checkbox"><span><strong>Enemy operatives deployed</strong><small>Confirm that your kill team has been placed in its drop zone.</small></span></label></div><div class="wizard-actions"><button class="btn ghost" id="setupBack">Back</button><button class="btn primary" id="setupNext" disabled>Continue</button></div>`;
    return `<h3>Setup complete</h3><div class="summary-box"><strong>${mission().number} · ${mission().name}</strong><br>${state.roster.length} starting NPOs · ${state.enemyCount} Enemy operatives</div>${boardSvg(mission().id)}<p><strong>Mission objective:</strong> ${mission().objective}</p><p><strong>Special rule reminder:</strong> ${mission().special}</p><div class="wizard-actions"><button class="btn ghost" id="setupBack">Back</button><button class="btn primary" id="beginGame">Begin Turning Point 1</button></div>`;
  }

  function bindSetup(step){
    $$('.mission-choice').forEach(b=>b.onclick=()=>{state.missionId=b.dataset.mission;state.setupChecks=[];state.roster=[];save();render();});
    $('#setupHome')?.addEventListener('click',()=>{state.screen='home';save();render();});
    $('#setupBack')?.addEventListener('click',()=>{state.setupStep=Math.max(0,state.setupStep-1);save();render();});
    $('#setupNext')?.addEventListener('click',()=>{state.setupStep=Math.min(5,state.setupStep+1);save();render();});
    $$('[data-check]').forEach(c=>c.onchange=()=>{state.setupChecks[Number(c.dataset.check)]=c.checked;save();render();});
    $('#generateBtn')?.addEventListener('click',()=>{generateRoster();save();render();});
    $$('[data-deploy]').forEach(b=>b.onclick=()=>{const n=state.roster.find(x=>x.id===b.dataset.deploy);n.deployed=!n.deployed;save();render();});
    $('#enemyCount')?.addEventListener('change',e=>{state.enemyCount=Math.max(1,Math.min(20,Number(e.target.value)||1));state.enemyReady=state.enemyCount;save();});
    $('#enemyDeployed')?.addEventListener('change',e=>{$('#setupNext').disabled=!e.target.checked;});
    $('#beginGame')?.addEventListener('click',()=>{
      state.screen='game';
      state.tab='play';
      state.turningPoint=0;
      state.phase='between';
      state.nextSide='enemy';
      state.enemyReady=state.enemyCount;
      state.roster.forEach(n=>n.ready=false);
      log(`Mission started: ${mission().name}.`);
      startTurningPoint();
    });
  }

  function renderGame(){
    $$('#bottomNav button').forEach(b=>b.classList.toggle('active',b.dataset.nav===state.tab));
    if(state.tab==='play') renderPlay();
    else if(state.tab==='mission') renderMission();
    else if(state.tab==='roster') renderRoster();
    else if(state.tab==='journal') renderJournal();
    else renderHelp();
  }

  function hud(){return `<div class="hud"><div><small>Turning Point</small><strong>${state.turningPoint||'Setup'}</strong></div><div><small>Threat</small><strong>${state.threat}</strong></div><div><small>Grade</small><strong>${threatGrade()}</strong></div><div><small>Enemy Ready</small><strong>${state.enemyReady}</strong></div><div><small>NPO Ready</small><strong>${readyNpos().length}</strong></div></div><div class="threat-strip"><div><strong>${threatLabel()}</strong><small>${threatGrade()===3?'Maximum grade':`${threatToNext()} Threat to next grade`}</small></div><div class="threat-meter"><span style="width:${(state.threat/15)*100}%"></span></div><button class="mini-btn" id="threatDown" aria-label="Decrease Threat">−</button><button class="mini-btn" id="threatUp" aria-label="Increase Threat">+</button></div>`;}

  function renderPlay(){
    app.innerHTML=hud()+`<div class="phase-track"><span class="${state.phase==='strategy'?'current':''}">Strategy</span>›<span class="${state.phase==='firefight'?'current':''}">Activations</span>›<span class="${state.phase==='end'?'current':''}">End Turning Point</span></div>${nextStepCard()}${state.phase==='firefight'?activationTracker():''}`;
    bindPlay();
  }

  function nextStepCard(){
    if(state.completed) return `<section class="next-card"><span class="phase">MISSION COMPLETE</span><h2>Record the outcome</h2><p>The mission has reached its conclusion. Review the Journal or begin a new game.</p><button class="btn primary big-action" id="newGameFromPlay">Start New Game</button></section>`;
    if(state.phase==='between') return `<section class="next-card"><span class="phase">NEXT STEP</span><h2>Start Turning Point ${state.turningPoint+1}</h2><p>The Guide will ready operatives, determine the current Threat Grade, generate reinforcements, check Tomb World events, and resolve initiative.</p><button class="btn primary big-action" id="startTp">Start Next Turning Point</button></section>`;
    if(state.phase==='strategy') return strategyCard();
    if(state.phase==='end') return `<section class="next-card"><span class="phase">END OF TURNING POINT</span><h2>Score and clean up</h2><p>Score mission objectives, resolve end-of-turn effects, and confirm all temporary markers have been cleared.</p><div class="field"><label>Mission progress: ${mission().tracker}</label><input id="tracker" type="number" min="0" max="${mission().max}" value="${state.tracker}"></div><div class="checklist"><label class="check-row"><input id="endChecked" type="checkbox"><span><strong>End-of-turn steps complete</strong><small>Objectives scored, temporary effects resolved, and physical tokens cleaned up.</small></span></label></div><button class="btn primary big-action" id="finishTp" disabled>Finish Turning Point</button></section>`;
    if(state.enemyReady<=0 && readyNpos().length===0){ state.phase='end'; save(); return nextStepCard(); }
    if(state.nextSide==='enemy' && state.enemyReady>0) return `<section class="next-card"><span class="phase">FIREFIGHT PHASE · ACTIVATION ${state.activationNumber+1}</span><h2>Activate an Enemy operative</h2><p>Resolve one of your solo player-controlled operatives on the tabletop, then record what happened so Threat and alternation remain accurate.</p><button class="btn primary big-action" id="enemyActivation">Record Enemy Activation</button><button class="btn ghost big-action" id="skipEnemy">No Enemy Operatives Ready</button></section>`;
    if(readyNpos().length>0){const n=nextNpo();return `<section class="next-card"><span class="phase">NPO ACTIVATION · ACTIVATION ${state.activationNumber+1}</span><h2>${escapeHtml(n.name)}</h2><p>${n.type} · ${n.behavior} · ${n.wounds}/${n.maxWounds} wounds</p><div class="summary-box"><strong>Next step:</strong> answer a short set of battlefield questions from this NPO’s perspective.</div><button class="btn primary big-action" id="npoActivation">Guide This NPO</button></section>`;}
    if(state.enemyReady>0){state.nextSide='enemy';save();return nextStepCard();}
    state.phase='end';save();return nextStepCard();
  }

  function strategyCard(){
    const d=state.strategyData||{};
    if(state.strategyStage==='summary'){
      const rolls=(d.reinforcements||[]).map(r=>`<div class="reinforcement-result"><div class="dice-row compact">${r.rolls.map(v=>dieHtml({value:v,kind:'hit'})).join('')}</div><strong>${r.type}</strong></div>`).join('');
      return `<section class="next-card"><span class="phase">STRATEGY PHASE · STEP 1 OF 2</span><h2>Turning Point ${state.turningPoint} prepared</h2><div class="stat-grid"><div class="stat"><small>Threat</small><strong>${state.threat}</strong></div><div class="stat"><small>Grade</small><strong>${d.grade??threatGrade()}</strong></div><div class="stat"><small>NPOs Ready</small><strong>${readyNpos().length}</strong></div><div class="stat"><small>Reinforcements</small><strong>${(d.reinforcements||[]).length}</strong></div></div>${rolls?`<h3>Reinforcements generated</h3><div class="reinforcement-grid">${rolls}</div><div class="field"><label>Reinforcement entry point</label><select id="reinforcementEntry"><option>Nearest valid entry point</option><option>Entry Point A</option><option>Entry Point B</option><option>Entry Point C</option><option>Custom placement</option></select></div>`:'<div class="summary-box"><strong>No reinforcements arrive.</strong></div>'}${d.blocked?`<p class="warning-text">${d.blocked} reinforcement(s) were blocked by the 10-NPO battlefield limit.</p>`:''}${d.event?`<div class="summary-box"><strong>${d.event[0]}</strong><br>${d.event[1]}</div>`:'<p>No Tomb World event is required.</p>'}<button class="btn primary big-action" id="continueStrategy">Continue to Initiative</button></section>`;
    }
    const auto=state.threat===0;
    return `<section class="next-card"><span class="phase">STRATEGY PHASE · STEP 2 OF 2</span><h2>${auto?'Enemy automatically has initiative':'Determine initiative'}</h2>${auto?`<p>At Threat 0, the tomb remains dormant. NPOs are expended and the Enemy begins the Firefight Phase.</p>`:`<p>The Guide rolled once for each side. Use the result, reroll both dice, or override it if your tabletop rules require a different outcome.</p><div class="initiative-roll"><div><small>Enemy</small>${dieHtml({value:state.strategyData.enemyRoll,kind:'hit'})}</div><div><small>NPOs</small>${dieHtml({value:state.strategyData.npoRoll,kind:'hit'})}</div></div><div class="summary-box"><strong>${state.strategyData.suggestedInitiative==='npo'?'NPOs':'Enemy'} win initiative${state.strategyData.enemyRoll===state.strategyData.npoRoll?' after the tie-break':''}.</strong></div>`}<div class="quick-actions">${auto?'':`<button class="btn ghost" id="rerollInitiative">Reroll Both</button>`}<button class="btn primary" data-init="enemy">Begin with Enemy</button><button class="btn secondary" data-init="npo" ${auto?'disabled':''}>Begin with NPOs</button></div></section>`;
  }

  function activationTracker(){
    const enemySpent=state.enemyCount-state.enemyReady;
    const enemyDots=Array.from({length:state.enemyCount},(_,i)=>`<span class="activation-dot ${i<enemySpent?'spent':'ready'}" title="Enemy operative ${i+1}"></span>`).join('');
    const npoRows=activeNpos().map(n=>`<div class="tracker-npo ${n.ready?'ready':'spent'}"><span>${escapeHtml(n.name)}</span><strong>${n.ready?'READY':'EXPENDED'}</strong></div>`).join('');
    return `<section class="card activation-tracker"><div class="panel-title"><div><p class="eyebrow">ACTIVATION TRACKER</p><h3>${state.activationNumber} activations completed</h3></div><div class="turn-badge">Next: ${state.nextSide==='npo'?'NPO':'Enemy'}</div></div><div class="tracker-section"><small>Enemy operatives</small><div class="enemy-dots">${enemyDots}</div></div><div class="tracker-section"><small>NPOs</small><div class="tracker-npos">${npoRows||'<span class="muted">No active NPOs</span>'}</div></div></section>`;
  }

  function bindPlay(){
    $('#startTp')?.addEventListener('click',startTurningPoint);
    $('#continueStrategy')?.addEventListener('click',()=>{state.reinforcementEntry=$('#reinforcementEntry')?.value||state.reinforcementEntry;state.strategyStage='initiative';save();render();});
    $('#rerollInitiative')?.addEventListener('click',()=>{rollInitiative();save();render();});
    $$('[data-init]').forEach(b=>b.onclick=()=>beginFirefight(b.dataset.init));
    $('#enemyActivation')?.addEventListener('click',()=>showEnemyActivation());
    $('#skipEnemy')?.addEventListener('click',()=>{state.enemyReady=0;state.nextSide=readyNpos().length?'npo':'enemy';log('No Enemy operatives remain ready.');save();render();});
    $('#npoActivation')?.addEventListener('click',showNpoWizard);
    $('#tracker')?.addEventListener('change',e=>{state.tracker=Math.max(0,Math.min(mission().max,Number(e.target.value)||0));save();});
    $('#endChecked')?.addEventListener('change',e=>{$('#finishTp').disabled=!e.target.checked;});
    $('#finishTp')?.addEventListener('click',()=>{state.phase='between';state.strategyStage=null;state.strategyData=null;state.newIds=[];log(`Turning Point ${state.turningPoint} completed.`);save();render();});
    $('#newGameFromPlay')?.addEventListener('click',confirmNewGame);
    $('#threatUp')?.addEventListener('click',()=>{setThreat(1,'Manual adjustment');save();render();});
    $('#threatDown')?.addEventListener('click',()=>{setThreat(-1,'Manual adjustment');save();render();});
  }

  function startTurningPoint(){
    state.turningPoint++;
    state.enemyReady=state.enemyCount;
    state.enemyActivated=0;state.npoActivated=0;state.activationNumber=0;state.activationHistory=[];
    const grade=threatGrade();
    activeNpos().forEach(n=>n.ready=state.threat>0);
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
    state.strategyData={grade,reinforcements,blocked,event,enemyRoll:null,npoRoll:null,suggestedInitiative:'enemy'};
    rollInitiative();
    state.phase='strategy';state.strategyStage='summary';state.nextSide='enemy';state.activeNpoId=null;
    log(`Turning Point ${state.turningPoint} started. Grade ${grade}; ${reinforcements.length} reinforcement(s).`);
    save();render();
  }

  function rollInitiative(){
    if(!state.strategyData)state.strategyData={};
    if(state.threat===0){state.strategyData.enemyRoll=null;state.strategyData.npoRoll=null;state.strategyData.suggestedInitiative='enemy';return;}
    const e=roll(),n=roll();state.strategyData.enemyRoll=e;state.strategyData.npoRoll=n;
    state.strategyData.suggestedInitiative=n>e?'npo':'enemy';
  }

  function beginFirefight(side){
    state.initiative=side;state.phase='firefight';state.strategyStage=null;state.nextSide=side;
    if(state.threat===0)activeNpos().forEach(n=>n.ready=false);
    log(`${side==='npo'?'NPOs':'Enemy'} begin the Firefight Phase with initiative.`);save();render();
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

  function showEnemyActivation(stage={}){
    const living=activeNpos();
    const checked=key=>stage[key]?'checked':'';
    const shootResolved=Boolean(stage.shootResolved);
    const meleeResolved=Boolean(stage.meleeResolved);
    showModal('Record Enemy Activation',`<p>Select everything that occurred during this Enemy operative’s activation. Movement actions do not increase Threat, but recording them keeps the activation history clear.</p>
      <div class="activation-groups">
        <section class="activation-group">
          <div class="activation-group-title"><span>↔</span><div><strong>Movement</strong><small>Position and control actions</small></div></div>
          <div class="toggle-list enemy-action-list">
            <label><input type="checkbox" id="eaMove" ${checked('move')}>Move</label>
            <label><input type="checkbox" id="eaDash" ${checked('dash')}>Dash</label>
            <label><input type="checkbox" id="eaCharge" ${checked('charge')}>Charge</label>
            <label><input type="checkbox" id="eaFallBack" ${checked('fallBack')}>Fall Back</label>
          </div>
        </section>

        <section class="activation-group">
          <div class="activation-group-title"><span>⚔</span><div><strong>Combat</strong><small>Record and resolve attacks</small></div></div>
          <div class="combat-action-card">
            <label><input type="checkbox" id="eaShoot" ${checked('shoot')}><span><strong>Shoot</strong><small>Use a non-Silent ranged weapon</small></span></label>
            <div class="inline-resolver ${stage.shoot?'':'hidden'}" id="shootResolver">
              ${living.length?`<button class="btn secondary" id="resolveShoot">Resolve Shooting Attack</button><small>${shootResolved?'Shooting attack resolved.':'Optional... open the attack wizard to roll dice and apply damage.'}</small>`:'<small>No active NPO is available as a target.</small>'}
            </div>
          </div>
          <div class="combat-action-card">
            <label><input type="checkbox" id="eaMelee" ${checked('melee')||checked('fight')}><span><strong>Melee</strong><small>Use the Kill Team Fight action</small></span></label>
            <div class="inline-resolver ${(stage.melee||stage.fight)?'':'hidden'}" id="meleeResolver">
              ${living.length?`<button class="btn secondary" id="resolveMelee">Resolve Melee Attack</button><small>${meleeResolved?'Melee attack resolved.':'Optional... open the attack wizard to roll dice and apply damage.'}</small>`:'<small>No active NPO is available as a target.</small>'}
            </div>
          </div>
          <div class="toggle-list enemy-action-list compact-actions">
            <label><input type="checkbox" id="eaDamage" ${checked('damage')}>Damaged an NPO with another action</label>
          </div>
        </section>

        <section class="activation-group">
          <div class="activation-group-title"><span>▣</span><div><strong>Battlefield</strong><small>Terrain and mission interactions</small></div></div>
          <div class="toggle-list enemy-action-list">
            <label><input type="checkbox" id="eaHatch" ${checked('hatch')}>Operate Hatch</label>
            <label><input type="checkbox" id="eaBreach" ${checked('breach')}>Breach</label>
            <label><input type="checkbox" id="eaObjective" ${checked('objective')}>Mission or objective action</label>
          </div>
        </section>

        <section class="activation-group pass-group">
          <div class="toggle-list enemy-action-list">
            <label><input type="checkbox" id="eaPass" ${checked('pass')}>Pass / no action recorded</label>
          </div>
        </section>
      </div>
      <div class="wizard-actions"><button class="btn ghost" data-close>Cancel</button><button class="btn primary" id="confirmEnemy">Complete Activation</button></div>`);

    const actionIds=['eaMove','eaDash','eaCharge','eaFallBack','eaShoot','eaMelee','eaDamage','eaHatch','eaBreach','eaObjective'];
    const clearPass=()=>{if($('#eaPass'))$('#eaPass').checked=false;};
    $('#eaPass')?.addEventListener('change',e=>{
      if(e.target.checked){
        actionIds.forEach(id=>{const box=$(`#${id}`);if(box)box.checked=false;});
        $('#shootResolver')?.classList.add('hidden');
        $('#meleeResolver')?.classList.add('hidden');
      }
    });
    actionIds.forEach(id=>$(`#${id}`)?.addEventListener('change',e=>{
      if(e.target.checked)clearPass();
    }));
    $('#eaShoot')?.addEventListener('change',e=>$('#shootResolver')?.classList.toggle('hidden',!e.target.checked));
    $('#eaMelee')?.addEventListener('change',e=>$('#meleeResolver')?.classList.toggle('hidden',!e.target.checked));

    $('#resolveShoot')?.addEventListener('click',()=>{
      const nextStage=readEnemyActivationStage(shootResolved,meleeResolved);
      showEnemyAttackWizard(null,()=>showEnemyActivation({...nextStage,shootResolved:true}),'shoot');
    });
    $('#resolveMelee')?.addEventListener('click',()=>{
      const nextStage=readEnemyActivationStage(shootResolved,meleeResolved);
      showEnemyAttackWizard(null,()=>showEnemyActivation({...nextStage,meleeResolved:true}),'melee');
    });
    $('#confirmEnemy').onclick=()=>{
      const finalStage=readEnemyActivationStage(shootResolved,meleeResolved);
      const hasRecordedAction=enemyActivationHasAction(finalStage);
      if(!hasRecordedAction){
        showModal('No actions selected',`<p>Mark this Enemy operative as activated without recording an action?</p><div class="wizard-actions"><button class="btn ghost" id="returnEnemyActivation">Go Back</button><button class="btn primary" id="confirmEmptyEnemyActivation">Complete Activation</button></div>`);
        $('#returnEnemyActivation').onclick=()=>showEnemyActivation(finalStage);
        $('#confirmEmptyEnemyActivation').onclick=()=>completeEnemyActivation(finalStage);
        return;
      }
      completeEnemyActivation(finalStage);
    };
  }

  function readEnemyActivationStage(shootResolved=false,meleeResolved=false){
    return {
      move:Boolean($('#eaMove')?.checked),
      dash:Boolean($('#eaDash')?.checked),
      charge:Boolean($('#eaCharge')?.checked),
      fallBack:Boolean($('#eaFallBack')?.checked),
      shoot:Boolean($('#eaShoot')?.checked),
      melee:Boolean($('#eaMelee')?.checked),
      damage:Boolean($('#eaDamage')?.checked),
      hatch:Boolean($('#eaHatch')?.checked),
      breach:Boolean($('#eaBreach')?.checked),
      objective:Boolean($('#eaObjective')?.checked),
      pass:Boolean($('#eaPass')?.checked),
      shootResolved:Boolean(shootResolved),
      meleeResolved:Boolean(meleeResolved)
    };
  }

  function enemyActivationHasAction(stage){
    return Boolean(stage.shootResolved || stage.meleeResolved || stage.move || stage.dash || stage.charge || stage.fallBack ||
      stage.shoot || stage.melee || stage.damage || stage.hatch || stage.breach || stage.objective || stage.pass);
  }

  function enemyActivationSummary(stage){
    const actions=[];
    if(stage.move)actions.push('Move');
    if(stage.dash)actions.push('Dash');
    if(stage.charge)actions.push('Charge');
    if(stage.fallBack)actions.push('Fall Back');
    if(stage.shoot)actions.push(stage.shootResolved?'Shooting attack resolved':'Shoot');
    if(stage.melee)actions.push(stage.meleeResolved?'Melee attack resolved':'Melee');
    if(stage.damage)actions.push('Damaging action');
    if(stage.hatch)actions.push('Operate Hatch');
    if(stage.breach)actions.push('Breach');
    if(stage.objective)actions.push('Mission action');
    if(stage.pass)actions.push('Pass / no action recorded');
    return actions.length?actions.join(', '):'No actions recorded';
  }

  function completeEnemyActivation(stage={}){
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
    if(inc)setThreat(inc,'Enemy activation');
    state.enemyReady=Math.max(0,state.enemyReady-1);
    state.enemyActivated++;
    state.activationNumber++;
    const summary=enemyActivationSummary(stage);
    state.activationHistory.unshift({side:'enemy',label:`Enemy activation ${state.enemyActivated}`,summary});
    state.nextSide=readyNpos().length?'npo':'enemy';
    log(`Enemy operative completed activation ${state.enemyActivated}: ${summary}.`);
    closeModal();
    save();
    render();
  }

  function showEnemyAttackWizard(targetId,onDone,attackType='attack'){
    const targets=activeNpos(); if(!targets.length){showToast('No active NPO is available as a target.');return;}
    const attackLabel=attackType==='shoot'?'Shooting':attackType==='melee'?'Melee':'Enemy';
    showModal(`${attackLabel} Attack Wizard`,`<p>Enter the ${attackType==='melee'?'melee weapon':'weapon'} profile. The Guide will roll the attack, roll the selected NPO’s saves, and preview damage before you confirm it.</p>
      <div class="field"><label>Target NPO</label><select id="combatTarget">${targets.map(n=>`<option value="${n.id}" ${n.id===targetId?'selected':''}>${escapeHtml(n.name)} · ${n.wounds}/${n.maxWounds} wounds · Save ${n.save}+</option>`).join('')}</select></div>
      <div class="combat-grid">
        ${spinnerField('enemyAttackDice','Attack dice',4,1,12)}
        ${spinnerField('enemyHit','Hit on',3,2,6)}
        ${spinnerField('enemyNormalDamage','Normal damage',3,0,12)}
        ${spinnerField('enemyCritDamage','Critical damage',4,0,15)}
        ${spinnerField('enemyAp','AP',0,0,3)}
        ${spinnerField('npoDefenseDice','NPO Defense Dice',3,0,6)}
      </div>
      <label class="check-row compact-check"><input type="checkbox" id="npoCover"><span><strong>NPO retains one normal save for cover</strong></span></label>
      <div id="combatResults" class="combat-results"><p>Set the profile, then roll the attack.</p></div>
      <div class="wizard-actions"><button class="btn ghost" data-close>Cancel</button><button class="btn primary" id="rollEnemyAttack">Roll Attack & Saves</button></div>`);
    bindSpinners(modal);
    $('#rollEnemyAttack').onclick=()=>rollEnemyAttackPreview(onDone);
  }

  function rollEnemyAttackPreview(onDone){
    const n=state.roster.find(x=>x.id===$('#combatTarget').value); if(!n)return;
    const profile={dice:num('enemyAttackDice'),hit:num('enemyHit'),normal:num('enemyNormalDamage'),crit:num('enemyCritDamage')};
    const attackDice=rollAttack(profile);
    const defense=resolveDefense(attackDice,num('npoDefenseDice'),n.save,num('enemyAp'),$('#npoCover').checked,profile);
    const before=n.wounds,after=Math.max(0,before-defense.damage);
    const box=$('#combatResults');
    box.innerHTML=`<div class="combat-stage"><small>ENEMY ATTACK DICE</small><div class="dice-row animated-roll" id="enemyAttackDiceResult">${attackDice.map(()=>rollingDieHtml()).join('')}</div></div>
      <div class="combat-stage"><small>NPO SAVE DICE</small><div class="dice-row animated-roll" id="npoSaveDiceResult">${defense.saveDice.map(()=>rollingDieHtml()).join('')||'<span class="muted">No save dice rolled</span>'}</div>${defense.coverRetained?'<span class="cover-retain">+ 1 retained normal cover save</span>':''}</div>
      <div class="damage-summary"><div><small>Unsaved normal hits</small><strong>${defense.normalRemaining}</strong></div><div><small>Unsaved critical hits</small><strong>${defense.critRemaining}</strong></div><div><small>Damage</small><strong>${defense.damage}</strong></div><div><small>Wounds after confirmation</small><strong>${before} → ${after}</strong></div></div>
      <p class="muted">Damage is only applied after you press Confirm Damage.</p>`;
    $('#rollEnemyAttack').textContent='Confirm Damage';
    $('#rollEnemyAttack').onclick=()=>{
      n.wounds=after;if(n.wounds===0)n.ready=false;
      log(`Enemy attack dealt ${defense.damage} damage to ${n.name} (${before} → ${after} wounds).`);
      save();closeModal();showToast(`${n.name}: ${defense.damage} damage confirmed.`);if(onDone)onDone();else render();
    };
    setTimeout(()=>{
      const a=$('#enemyAttackDiceResult');if(a){a.innerHTML=attackDice.map(dieHtml).join('');a.classList.add('settled');}
      const d=$('#npoSaveDiceResult');if(d&&defense.saveDice.length){d.innerHTML=defense.saveDice.map(dieHtml).join('');d.classList.add('settled');}
    },700);
  }

  const npoQuestions = [
    {key:'engaged',title:'Is an Enemy operative in control range?',help:'Choose Yes when this NPO can immediately Fight an Enemy operative without moving.'},
    {key:'charge',title:'Can this NPO complete a Charge?',help:'Choose Yes only when a legal Charge can finish within control range of an Enemy operative.'},
    {key:'shot',title:'Does this NPO have a valid shooting target?',help:'The target must be valid for the NPO’s ranged weapon after any movement you expect it to make.'},
    {key:'objective',title:'Is an Enemy operative controlling a mission objective?',help:'This gives mission denial priority over an otherwise equal target.'},
    {key:'wounded',title:'Is a valid Enemy target wounded?',help:'A wounded target is below its starting wounds and can reasonably be attacked by this NPO.'},
    {key:'hatch',title:'Does a closed hatch block the best route?',help:'Choose Yes when operating the hatch is the clearest way to advance toward an Enemy or objective.'},
    {key:'cover',title:'Can the NPO remain in cover while acting?',help:'This affects whether the Guide recommends holding position, moving minimally, or advancing aggressively.'},
    {key:'clustered',title:'Are multiple valid Enemy targets clustered together?',help:'This is used as a final target-priority tie breaker for pressure and board control.'}
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
    let action,target='closest valid Enemy operative',stance='Engage',threat=0,reason='Advance pressure toward the nearest relevant target.';
    if(c.objective){target='Enemy operative controlling the mission objective';path.push('Mission objective is threatened');}
    else if(c.wounded){target='wounded valid Enemy operative';path.push('A wounded target can be finished');}
    else if(c.clustered){target='the Enemy target in the largest cluster';path.push('Clustered targets offer the most board pressure');}
    else path.push('Use the closest valid Enemy operative');

    if(c.engaged){
      action='Fight the selected target, then reposition toward cover or the mission objective';
      reason='An Enemy is already in control range, so immediate melee takes priority.';threat=1;path.unshift('Enemy in control range → Fight');
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
    const decision=chooseNpoDecision(n,c);
    const attacks=decision.action.includes('Fight')||decision.action.includes('Shoot');
    const dice=attacks?rollAttack(n.attack):[];
    if(decision.threat)setThreat(decision.threat,`${n.name} ${decision.action.includes('Fight')?'Fight':'Shoot'}`);
    n.ready=false;state.npoActivated++;state.activationNumber++;
    state.activationHistory.unshift({side:'npo',label:n.name,action:decision.action});
    state.activeNpoId=null;state.nextSide=state.enemyReady>0?'enemy':'npo';
    state.lastActivation={name:n.name,...decision,dice,answers:c};
    log(`${n.name}: ${decision.action}.`);save();

    modalBody.innerHTML=`<div class="modal-inner ai-result">
      <p class="eyebrow">RECOMMENDED ACTIVATION</p>
      <div class="ai-result-title"><div><h2>${escapeHtml(n.name)}</h2><p>${escapeHtml(n.type)} · ${escapeHtml(n.behavior)}</p></div><span class="order-badge">${decision.stance}</span></div>
      <div class="activation-command"><small>ACTION SEQUENCE</small><strong>${escapeHtml(decision.action)}</strong></div>
      <div class="target-command"><small>TARGET PRIORITY</small><strong>${escapeHtml(decision.target)}</strong></div>
      ${dice.length?`<h3>Attack roll</h3><div class="dice-row animated-roll" id="aiDice">${dice.map(()=>rollingDieHtml()).join('')}</div><p id="aiDiceSummary" class="muted">Rolling ${dice.length} attack dice…</p><button class="btn secondary big-action" id="resolveNpoAttack">Resolve NPO Attack</button>`:''}
      <details class="decision-path"><summary>Why did the Guide choose this?</summary><p>${escapeHtml(decision.reason)}</p><ol>${decision.path.map(x=>`<li>${escapeHtml(x)}</li>`).join('')}</ol></details>
      <div class="wizard-actions"><button class="btn primary" id="completeNpo">Activation Complete</button></div>
    </div>`;
    if(dice.length){
      setTimeout(()=>{
        const box=$('#aiDice'); if(!box)return;
        box.innerHTML=dice.map(dieHtml).join('');box.classList.add('settled');
        const crits=dice.filter(d=>d.kind==='crit').length,hits=dice.filter(d=>d.kind==='hit').length,misses=dice.filter(d=>d.kind==='miss').length;
        $('#aiDiceSummary').textContent=`${crits} critical · ${hits} normal · ${misses} miss`;
      },850);
      $('#resolveNpoAttack').onclick=()=>showNpoAttackWizard(n,dice,()=>renderNpoResultAgain(n,decision,dice,c));
    }
    $('#completeNpo').onclick=()=>{closeModal();render();};
  }

  function renderNpoResultAgain(n,decision,dice,answers){
    state.lastActivation={name:n.name,...decision,dice,answers};save();
    showToast('NPO attack result recorded.');closeModal();render();
  }

  function showNpoAttackWizard(n,attackDice,onDone){
    showModal('NPO Attack Wizard',`<p>${escapeHtml(n.name)} rolled the attack dice shown below. Enter the Enemy operative’s defense profile to resolve saves and damage.</p>
      <div class="combat-stage"><small>NPO ATTACK DICE</small><div class="dice-row">${attackDice.map(dieHtml).join('')}</div><p>${n.attack.normal}/${n.attack.crit} damage · Hit ${n.attack.hit}+</p></div>
      <div class="combat-grid">
        ${spinnerField('enemyDefenseDice','Enemy Defense Dice',3,0,6)}
        ${spinnerField('enemySave','Enemy Save',3,2,6)}
        ${spinnerField('npoAp','NPO AP',0,0,3)}
        ${spinnerField('enemyWounds','Enemy wounds remaining',10,1,30)}
      </div>
      <label class="check-row compact-check"><input type="checkbox" id="enemyCover"><span><strong>Enemy retains one normal save for cover</strong></span></label>
      <div id="combatResults" class="combat-results"><p>Enter the defense profile, then roll saves.</p></div>
      <div class="wizard-actions"><button class="btn ghost" data-close>Cancel</button><button class="btn primary" id="rollNpoSaves">Roll Saves & Preview Damage</button></div>`);
    bindSpinners(modal);
    $('#rollNpoSaves').onclick=()=>{
      const before=num('enemyWounds');
      const result=resolveDefense(attackDice,num('enemyDefenseDice'),num('enemySave'),num('npoAp'),$('#enemyCover').checked,n.attack);
      const after=Math.max(0,before-result.damage);
      $('#combatResults').innerHTML=`<div class="combat-stage"><small>ENEMY SAVE DICE</small><div class="dice-row animated-roll" id="enemySaveDiceResult">${result.saveDice.map(()=>rollingDieHtml()).join('')||'<span class="muted">No save dice rolled</span>'}</div>${result.coverRetained?'<span class="cover-retain">+ 1 retained normal cover save</span>':''}</div><div class="damage-summary"><div><small>Unsaved normal hits</small><strong>${result.normalRemaining}</strong></div><div><small>Unsaved critical hits</small><strong>${result.critRemaining}</strong></div><div><small>Damage</small><strong>${result.damage}</strong></div><div><small>Enemy wounds</small><strong>${before} → ${after}</strong></div></div><p class="muted">Apply this wound change to the Enemy operative on the tabletop.</p>`;
      $('#rollNpoSaves').textContent='Confirm Result';
      $('#rollNpoSaves').onclick=()=>{log(`${n.name} dealt ${result.damage} damage to an Enemy operative (${before} → ${after} wounds).`);save();closeModal();if(onDone)onDone();};
      setTimeout(()=>{const d=$('#enemySaveDiceResult');if(d&&result.saveDice.length){d.innerHTML=result.saveDice.map(dieHtml).join('');d.classList.add('settled');}},700);
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

  function renderMission(){const m=mission();app.innerHTML=`<div class="panel-title"><div><p class="eyebrow">MISSION</p><h2>${m.number} · ${m.name}</h2><p>${m.brief}</p></div></div><section class="card"><h3>Objective</h3><p>${m.objective}</p><div class="stat-grid"><div class="stat"><small>Starting NPOs</small><strong>${m.setup}</strong></div><div class="stat"><small>${m.tracker}</small><strong>${state.tracker} / ${m.max}</strong></div></div></section>${boardSvg(m.id)}<section class="card"><h3>Special rule reminder</h3><p>${m.special}</p></section><section class="card"><p class="eyebrow">SESSION</p><div class="session-actions"><button class="btn danger" id="newGameSession">Start New Game</button><button class="btn secondary" id="exportSave">Export Save</button><button class="btn secondary" id="importSave">Import Save</button></div></section>`;$('#newGameSession').onclick=confirmNewGame;$('#exportSave').onclick=exportSave;$('#importSave').onclick=()=>importInput.click();}
  function renderRoster(){app.innerHTML=`<div class="panel-title"><div><p class="eyebrow">NPO ROSTER</p><h2>${activeNpos().length} active NPOs</h2><p>Wounds and Ready status update the guided activation flow.</p></div><button class="btn secondary" id="addNpo">Add NPO</button></div><div class="roster-grid">${state.roster.length?state.roster.map(n=>operativeCard(n,true)).join(''):'<div class="card empty">No NPOs are currently on the battlefield.</div>'}</div>`;$('#addNpo').onclick=showAddNpo;$$('[data-enemy-attack]').forEach(b=>b.onclick=()=>showEnemyAttackWizard(b.dataset.enemyAttack));$$('[data-wound]').forEach(b=>b.onclick=()=>adjustWounds(b.dataset.wound,-1));$$('[data-heal]').forEach(b=>b.onclick=()=>adjustWounds(b.dataset.heal,1));$$('[data-ready]').forEach(b=>b.onclick=()=>toggleReady(b.dataset.ready));$$('[data-delete]').forEach(b=>b.onclick=()=>deleteNpo(b.dataset.delete));}
  function operativeCard(n,controls){return `<article class="operative-card ${n.wounds<=0?'dead':''}"><h4>${escapeHtml(n.name)}</h4><p>${n.type} · ${n.behavior} · Save ${n.save}+</p><div class="wounds"><meter min="0" max="${n.maxWounds}" value="${n.wounds}"></meter><strong>${n.wounds}/${n.maxWounds}</strong></div><p>${n.ready&&n.wounds>0?'READY':'EXPENDED'}</p>${controls?`<div class="quick-actions"><button class="btn secondary" data-enemy-attack="${n.id}">Enemy Attack</button><button class="btn ghost" data-wound="${n.id}">− Wound</button><button class="btn ghost" data-heal="${n.id}">+ Heal</button><button class="btn secondary" data-ready="${n.id}">${n.ready?'Expend':'Ready'}</button><button class="btn danger" data-delete="${n.id}">Delete</button></div>`:''}</article>`;}
  function renderJournal(){app.innerHTML=`<div class="panel-title"><div><p class="eyebrow">JOURNAL</p><h2>Battle Record</h2><p>Automatic game-state and Threat history.</p></div><button class="btn ghost" id="clearJournal">Clear</button></div><section class="card"><ol class="activity-log">${state.journal.length?state.journal.map(j=>`<li><time>${new Date(j.time).toLocaleString()}</time>${escapeHtml(j.text)}</li>`).join(''):'<li>No events recorded.</li>'}</ol></section>`;$('#clearJournal').onclick=()=>{state.journal=[];save();render();};}
  function renderHelp(){app.innerHTML=`<div class="panel-title"><div><p class="eyebrow">FIELD HELP</p><h2>Quick explanations</h2><p>Open an item without leaving the current game.</p></div></div><section class="card help-list">
    <details><summary>What does Enemy mean?</summary><p>Your solo player-controlled Kill Team operatives. Prompts are written from an NPO’s perspective, so your models are the NPO’s enemies.</p></details>
    <details><summary>What is an NPO?</summary><p>A non-player operative controlled by the Guide’s decision tree.</p></details>
    <details><summary>What is Threat Level?</summary><p>A 0–15 alert meter that rises from loud or destructive actions. Higher Threat produces higher grades, more reinforcements, and eventually Tomb World events.</p></details>
    <details><summary>What is Threat Grade?</summary><p>Grade 0 at Threat 0, Grade 1 at 1–5, Grade 2 at 6–10, and Grade 3 at 11–15. Reinforcements normally equal the current grade after Turning Point 1.</p></details>
    <details><summary>When do I start the next Turning Point?</summary><p>After every ready Enemy operative and NPO has activated, complete end-of-turn scoring and press Finish Turning Point. The Play tab will then offer Start Next Turning Point.</p></details>
    <details><summary>What happens during the Strategy Phase?</summary><p>The Guide readies operatives, evaluates Threat Grade, generates reinforcements after Turning Point 1, checks for Tomb World events, and rolls initiative. You review each result before activations begin.</p></details>
    <details><summary>How does activation tracking work?</summary><p>Each completed Enemy or NPO activation is recorded. Ready counts and the next side update automatically. When both sides have no ready operatives, the Guide advances to end-of-turn scoring.</p></details>
    <details><summary>How are saves and damage handled?</summary><p>V1.3 includes guided Enemy and NPO attack wizards. Attack dice and save dice are rolled with visual pips, saves cancel hits, and damage is previewed before confirmation. Enemy attacks can update NPO wounds automatically.</p></details>
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
  function closeModal(){if(modal.open)modal.close();const cb=modal._onClose;modal._onClose=null;if(cb)cb();}
  modal.addEventListener('cancel',e=>{e.preventDefault();closeModal();});
  function showToast(text){toast.textContent=text;toast.hidden=false;clearTimeout(showToast.t);showToast.t=setTimeout(()=>toast.hidden=true,6500);}
  function confirmNewGame(){showModal('Start New Game?',`<p>This will replace the current mission, roster, Threat, Turning Point, and Journal.</p><div class="wizard-actions"><button class="btn ghost" data-close>Cancel</button><button class="btn danger" id="confirmNewGame">Start New Game</button></div>`);$('#confirmNewGame').onclick=()=>{localStorage.removeItem(STORAGE_KEY);state=initialState();state.screen='setup';closeModal();save();render();};}
  function exportSave(){const blob=new Blob([JSON.stringify(state,null,2)],{type:'application/json'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='tomb-world-solo-guide-save.json';a.click();URL.revokeObjectURL(a.href);}
  importInput.addEventListener('change',async()=>{const f=importInput.files?.[0];if(!f)return;try{const data=JSON.parse(await f.text());if(!data.version)throw new Error();state=normalizeState(data);state.screen='game';save();render();showToast('Save imported.');}catch{showToast('That file is not a valid Tomb World Solo Guide save.');}finally{importInput.value='';}});

  function bindCommon(){
    $$('#bottomNav button').forEach(b=>b.onclick=()=>{state.tab=b.dataset.nav;save();render();});
  }

  render();
})();

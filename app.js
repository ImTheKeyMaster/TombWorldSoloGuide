(() => {
  'use strict';

  const STORAGE_KEY = 'tombWorldSoloGuide.v1';
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
    version:1, screen:'home', tab:'play', setupStep:0, missionId:null,
    setupChecks:[], roster:[], enemyCount:6, enemyReady:6, turningPoint:0,
    threat:0, initiative:'enemy', phase:'setup', nextSide:'enemy', tracker:0,
    activeNpoId:null, journal:[], lastActivation:null, newIds:[], completed:false
  });

  let state = load() || initialState();

  function save(){ localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); }
  function load(){ try{return JSON.parse(localStorage.getItem(STORAGE_KEY));}catch{return null;} }
  function mission(){ return missions.find(m => m.id === state.missionId) || missions[0]; }
  function roll(sides=6){ return Math.floor(Math.random()*sides)+1; }
  function rollD3(){ return roll(3); }
  function uid(){ return `${Date.now().toString(36)}-${Math.random().toString(36).slice(2,7)}`; }
  function activeNpos(){ return state.roster.filter(n => n.wounds > 0); }
  function readyNpos(){ return activeNpos().filter(n => n.ready); }
  function threatGrade(){ return state.threat === 0 ? 0 : state.threat <= 5 ? 1 : state.threat <= 10 ? 2 : 3; }
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
      <img class="hero-symbol" src="assets/icon.svg" alt="">
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
    if(step===1){const m=mission();const checks=['Place walls and hatchways as shown','Place mission objective markers','Identify the Enemy drop zone','Identify NPO deployment areas'];return `<h3>${m.name} board setup</h3><p><strong>Objective:</strong> ${m.objective}</p>${boardSvg(m.id)}<div class="checklist">${checks.map((c,i)=>`<label class="check-row"><input type="checkbox" data-check="${i}" ${state.setupChecks[i]?'checked':''}><span><strong>${c}</strong><small>${i===0?'Use the schematic as a placement guide and the official terrain pieces for exact setup.':'Confirm this step on the physical board.'}</small></span></label>`).join('')}</div><div class="wizard-actions"><button class="btn ghost" id="setupBack">Back</button><button class="btn primary" id="setupNext" ${checks.every((_,i)=>state.setupChecks[i])?'':'disabled'}>Board Ready</button></div>`;}
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
    $('#beginGame')?.addEventListener('click',()=>{state.screen='game';state.tab='play';state.turningPoint=0;state.phase='between';state.nextSide='enemy';state.enemyReady=state.enemyCount;state.roster.forEach(n=>n.ready=false);log(`Mission started: ${mission().name}.`);save();render();});
  }

  function renderGame(){
    $$('#bottomNav button').forEach(b=>b.classList.toggle('active',b.dataset.nav===state.tab));
    if(state.tab==='play') renderPlay();
    else if(state.tab==='mission') renderMission();
    else if(state.tab==='roster') renderRoster();
    else if(state.tab==='journal') renderJournal();
    else renderHelp();
  }

  function hud(){return `<div class="hud"><div><small>Turning Point</small><strong>${state.turningPoint||'Setup'}</strong></div><div><small>Threat</small><strong>${state.threat}</strong></div><div><small>Grade</small><strong>${threatGrade()}</strong></div><div><small>Enemy Ready</small><strong>${state.enemyReady}</strong></div><div><small>NPO Ready</small><strong>${readyNpos().length}</strong></div></div>`;}

  function renderPlay(){
    app.innerHTML=hud()+`<div class="phase-track"><span class="${state.phase==='strategy'?'current':''}">Strategy</span>›<span class="${state.phase==='firefight'?'current':''}">Activations</span>›<span class="${state.phase==='end'?'current':''}">End Turning Point</span></div>${nextStepCard()}`;
    bindPlay();
  }

  function nextStepCard(){
    if(state.completed) return `<section class="next-card"><span class="phase">MISSION COMPLETE</span><h2>Record the outcome</h2><p>The mission has reached its conclusion. Review the Journal or begin a new game.</p><button class="btn primary big-action" id="newGameFromPlay">Start New Game</button></section>`;
    if(state.phase==='between') return `<section class="next-card"><span class="phase">NEXT STEP</span><h2>Start Turning Point ${state.turningPoint+1}</h2><p>The Guide will ready surviving NPOs, calculate Threat Grade, generate reinforcements after Turning Point 1, and check Tomb World events.</p><button class="btn primary big-action" id="startTp">Start Next Turning Point</button></section>`;
    if(state.phase==='strategy') return `<section class="next-card"><span class="phase">STRATEGY PHASE</span><h2>Resolve initiative</h2><p>Choose which side has initiative for this Turning Point. At Threat 0, the Enemy automatically has initiative and NPOs remain dormant.</p><div class="quick-actions"><button class="btn primary" data-init="enemy">Enemy Has Initiative</button><button class="btn secondary" data-init="npo" ${state.threat===0?'disabled':''}>NPOs Have Initiative</button></div></section>`;
    if(state.phase==='end') return `<section class="next-card"><span class="phase">END OF TURNING POINT</span><h2>Score and clean up</h2><p>Score mission objectives, resolve end-of-turn effects, and confirm all temporary markers have been cleared.</p><div class="field"><label>Mission progress: ${mission().tracker}</label><input id="tracker" type="number" min="0" max="${mission().max}" value="${state.tracker}"></div><div class="checklist"><label class="check-row"><input id="endChecked" type="checkbox"><span><strong>End-of-turn steps complete</strong><small>Objectives scored and temporary effects resolved.</small></span></label></div><button class="btn primary big-action" id="finishTp" disabled>Finish Turning Point</button></section>`;
    if(state.enemyReady<=0 && readyNpos().length===0){ state.phase='end'; save(); return nextStepCard(); }
    if(state.nextSide==='enemy' && state.enemyReady>0) return `<section class="next-card"><span class="phase">FIREFIGHT PHASE</span><h2>Activate an Enemy operative</h2><p>Resolve one of your solo player-controlled operatives on the tabletop, then tell the Guide what it did.</p><button class="btn primary big-action" id="enemyActivation">Record Enemy Activation</button><button class="btn ghost big-action" id="skipEnemy">No Enemy Operatives Ready</button></section>`;
    if(readyNpos().length>0){const n=nextNpo();return `<section class="next-card"><span class="phase">NPO ACTIVATION</span><h2>${escapeHtml(n.name)}</h2><p>${n.type} · ${n.behavior} · ${n.wounds}/${n.maxWounds} wounds</p><div class="summary-box"><strong>Next step:</strong> answer a short set of battlefield questions from this NPO’s perspective.</div><button class="btn primary big-action" id="npoActivation">Guide This NPO</button></section>`;}
    if(state.enemyReady>0){state.nextSide='enemy';save();return nextStepCard();}
    state.phase='end';save();return nextStepCard();
  }

  function bindPlay(){
    $('#startTp')?.addEventListener('click',startTurningPoint);
    $$('[data-init]').forEach(b=>b.onclick=()=>{state.initiative=b.dataset.init;state.phase='firefight';state.nextSide=state.initiative==='npo'?'npo':'enemy';log(`${state.initiative==='npo'?'NPOs':'Enemy'} gained initiative.`);save();render();});
    $('#enemyActivation')?.addEventListener('click',showEnemyActivation);
    $('#skipEnemy')?.addEventListener('click',()=>{state.enemyReady=0;state.nextSide='npo';save();render();});
    $('#npoActivation')?.addEventListener('click',showNpoWizard);
    $('#tracker')?.addEventListener('change',e=>{state.tracker=Math.max(0,Math.min(mission().max,Number(e.target.value)||0));save();});
    $('#endChecked')?.addEventListener('change',e=>{$('#finishTp').disabled=!e.target.checked;});
    $('#finishTp')?.addEventListener('click',()=>{state.phase='between';state.newIds=[];log(`Turning Point ${state.turningPoint} completed.`);save();render();});
    $('#newGameFromPlay')?.addEventListener('click',confirmNewGame);
  }

  function startTurningPoint(){
    state.turningPoint++;
    state.enemyReady=state.enemyCount;
    activeNpos().forEach(n=>n.ready=state.threat>0);
    const grade=threatGrade(), spawned=[];
    if(state.turningPoint>1 && grade>0){
      const slots=Math.max(0,MAX_NPOS-activeNpos().length), amount=Math.min(grade,slots);
      for(let i=0;i<amount;i++){const type=randomReinforcement();const p=profiles[type];const n={id:uid(),name:`${type} R${state.turningPoint}-${i+1}`,type,behavior:p.behavior,maxWounds:p.wounds,wounds:p.wounds,save:p.save,attack:{...p.attack},ready:true,deployed:true};state.roster.push(n);state.newIds.push(n.id);spawned.push(type);}
    }
    let event=null;
    if(grade===3){event=events[roll(events.length)-1]; if(event[0]==='Stirrings of Horror')setThreat(1,event[0]);}
    state.phase='strategy';state.nextSide='enemy';
    log(`Turning Point ${state.turningPoint} started. Grade ${grade}; ${spawned.length} reinforcement(s).`);
    save();
    showModal(`Turning Point ${state.turningPoint}`,`<div class="stat-grid"><div class="stat"><small>Threat</small><strong>${state.threat}</strong></div><div class="stat"><small>Grade</small><strong>${grade}</strong></div><div class="stat"><small>NPOs readied</small><strong>${readyNpos().length}</strong></div><div class="stat"><small>Reinforcements</small><strong>${spawned.length}</strong></div></div>${spawned.length?`<h3>Reinforcements</h3><p>${spawned.join(', ')}</p>`:'<p>No reinforcements arrive.</p>'}${event?`<div class="summary-box"><strong>${event[0]}</strong><br>${event[1]}</div>`:''}<div class="wizard-actions"><button class="btn primary" data-close>Resolve Initiative</button></div>`,()=>render());
  }

  function randomReinforcement(){ const r=roll(6)+roll(6); return r<=4?'Canoptek Scarab Swarm':r<=6?'Canoptek Macrocyte':r<=10?'Necron Warrior':'Canoptek Tomb Crawler'; }
  function nextNpo(){ let n=state.roster.find(x=>x.id===state.activeNpoId&&x.ready&&x.wounds>0); if(!n){n=readyNpos().sort((a,b)=>priority(b)-priority(a))[0];state.activeNpoId=n?.id||null;} return n; }
  function priority(n){return ({Guardian:4,Marksman:3,Brawler:2,Sentinel:1}[n.behavior]||1)+(n.wounds/n.maxWounds<.5?-.5:0);}

  function showEnemyActivation(){
    showModal('Record Enemy Activation',`<p>Select everything that occurred during this Enemy operative’s activation.</p><div class="toggle-list">
      <label><input type="checkbox" id="eaShoot">Used a non-Silent Shoot action</label>
      <label><input type="checkbox" id="eaFight">Used a Fight action</label>
      <label><input type="checkbox" id="eaDamage">Damaged an NPO with another action</label>
      <label><input type="checkbox" id="eaHatch">Operated a hatch</label>
      <label><input type="checkbox" id="eaBreach">Performed a Breach</label>
      <label><input type="checkbox" id="eaObjective">Interacted with a mission objective</label>
    </div><div class="wizard-actions"><button class="btn ghost" data-close>Cancel</button><button class="btn primary" id="confirmEnemy">Complete Activation</button></div>`);
    $('#confirmEnemy').onclick=()=>{
      let inc=0; if($('#eaShoot').checked)inc++; if($('#eaFight').checked)inc++; if($('#eaDamage').checked)inc++;
      if($('#eaHatch').checked){const r=roll();if(r>=4)inc++;showToast(`Operate Hatch rolled ${r}${r>=4?'... Threat +1':'... no Threat increase'}`);}
      if($('#eaBreach').checked){inc++;const r=roll();if(r>=4)inc++;showToast(`Breach rolled ${r}${r>=4?'... Threat +2 total':'... Threat +1 total'}`);}
      if(inc)setThreat(inc,'Enemy activation');
      state.enemyReady=Math.max(0,state.enemyReady-1);state.nextSide=readyNpos().length?'npo':'enemy';log('Enemy operative completed an activation.');closeModal();save();render();
    };
  }

  function showNpoWizard(){
    const n=nextNpo(); if(!n)return;
    showModal(`Guide ${escapeHtml(n.name)}`,`<p>Answer from this NPO’s current position.</p><div class="toggle-list">
      <label><input type="checkbox" id="nwEngaged">An Enemy is in control range</label>
      <label><input type="checkbox" id="nwCharge">Can complete a Charge</label>
      <label><input type="checkbox" id="nwShot" checked>Has a valid shooting target</label>
      <label><input type="checkbox" id="nwObjective">An Enemy controls a mission objective</label>
      <label><input type="checkbox" id="nwWounded">A valid Enemy target is wounded</label>
      <label><input type="checkbox" id="nwHatch">A closed hatch blocks the best route</label>
    </div><div class="wizard-actions"><button class="btn ghost" data-close>Cancel</button><button class="btn primary" id="decideNpo">Determine Activation</button></div>`);
    $('#decideNpo').onclick=()=>resolveNpo(n);
  }

  function resolveNpo(n){
    const c={engaged:$('#nwEngaged').checked,charge:$('#nwCharge').checked,shot:$('#nwShot').checked,objective:$('#nwObjective').checked,wounded:$('#nwWounded').checked,hatch:$('#nwHatch').checked};
    let action,target='closest visible Enemy operative',threat=0;
    if(c.engaged){action='Fight, then reposition toward cover or the mission objective';threat=1;}
    else if(c.charge&&(n.behavior==='Brawler'||c.objective)){action='Charge the highest-priority Enemy, then Fight';threat=1;}
    else if(c.shot){action='Move only if needed for line of sight, then Shoot';threat=1;}
    else if(c.hatch){action='Operate the blocking hatch, then move toward the nearest Enemy';}
    else action='Move toward the nearest Enemy or mission objective, retaining cover where possible';
    if(c.objective)target='Enemy operative controlling the mission objective';else if(c.wounded)target='wounded valid Enemy operative';
    const dice=action.includes('Fight')||action.includes('Shoot')?rollAttack(n.attack):[];
    if(threat)setThreat(threat,`${n.name} ${action.includes('Fight')?'Fight':'Shoot'}`);
    n.ready=false;state.activeNpoId=null;state.nextSide=state.enemyReady>0?'enemy':'npo';state.lastActivation={name:n.name,action,target,dice};log(`${n.name}: ${action}.`);save();
    modalBody.innerHTML=`<div class="modal-inner"><p class="eyebrow">RECOMMENDED ACTIVATION</p><h2>${escapeHtml(n.name)}</h2><div class="summary-box"><strong>${action}</strong><br>Target: ${target}</div>${dice.length?`<h3>Attack roll</h3><div class="dice-row">${dice.map(dieHtml).join('')}</div><p>${dice.filter(d=>d.kind==='crit').length} critical · ${dice.filter(d=>d.kind==='hit').length} normal · ${dice.filter(d=>d.kind==='miss').length} miss</p>`:''}<div class="wizard-actions"><button class="btn primary" id="completeNpo">Activation Complete</button></div></div>`;
    $('#completeNpo').onclick=()=>{closeModal();render();};
  }

  function rollAttack(profile){return Array.from({length:profile.dice},()=>{const value=roll();return{value,kind:value===6?'crit':value>=profile.hit?'hit':'miss'};});}
  const pipPositions={1:[5],2:[1,9],3:[1,5,9],4:[1,3,7,9],5:[1,3,5,7,9],6:[1,3,4,6,7,9]};
  function dieHtml(d){return `<div class="die ${d.kind}" aria-label="${d.value} ${d.kind}">${pipPositions[d.value].map(p=>`<span class="pip" style="grid-area:${Math.ceil(p/3)}/${((p-1)%3)+1}"></span>`).join('')}</div>`;}

  function renderMission(){const m=mission();app.innerHTML=`<div class="panel-title"><div><p class="eyebrow">MISSION</p><h2>${m.number} · ${m.name}</h2><p>${m.brief}</p></div></div><section class="card"><h3>Objective</h3><p>${m.objective}</p><div class="stat-grid"><div class="stat"><small>Starting NPOs</small><strong>${m.setup}</strong></div><div class="stat"><small>${m.tracker}</small><strong>${state.tracker} / ${m.max}</strong></div></div></section>${boardSvg(m.id)}<section class="card"><h3>Special rule reminder</h3><p>${m.special}</p></section><section class="card"><p class="eyebrow">SESSION</p><div class="session-actions"><button class="btn danger" id="newGameSession">Start New Game</button><button class="btn secondary" id="exportSave">Export Save</button><button class="btn secondary" id="importSave">Import Save</button></div></section>`;$('#newGameSession').onclick=confirmNewGame;$('#exportSave').onclick=exportSave;$('#importSave').onclick=()=>importInput.click();}
  function renderRoster(){app.innerHTML=`<div class="panel-title"><div><p class="eyebrow">NPO ROSTER</p><h2>${activeNpos().length} active NPOs</h2><p>Wounds and Ready status update the guided activation flow.</p></div><button class="btn secondary" id="addNpo">Add NPO</button></div><div class="roster-grid">${state.roster.length?state.roster.map(n=>operativeCard(n,true)).join(''):'<div class="card empty">No NPOs are currently on the battlefield.</div>'}</div>`;$('#addNpo').onclick=showAddNpo;$$('[data-wound]').forEach(b=>b.onclick=()=>adjustWounds(b.dataset.wound,-1));$$('[data-heal]').forEach(b=>b.onclick=()=>adjustWounds(b.dataset.heal,1));$$('[data-ready]').forEach(b=>b.onclick=()=>toggleReady(b.dataset.ready));$$('[data-delete]').forEach(b=>b.onclick=()=>deleteNpo(b.dataset.delete));}
  function operativeCard(n,controls){return `<article class="operative-card ${n.wounds<=0?'dead':''}"><h4>${escapeHtml(n.name)}</h4><p>${n.type} · ${n.behavior} · Save ${n.save}+</p><div class="wounds"><meter min="0" max="${n.maxWounds}" value="${n.wounds}"></meter><strong>${n.wounds}/${n.maxWounds}</strong></div><p>${n.ready&&n.wounds>0?'READY':'EXPENDED'}</p>${controls?`<div class="quick-actions"><button class="btn ghost" data-wound="${n.id}">− Wound</button><button class="btn ghost" data-heal="${n.id}">+ Heal</button><button class="btn secondary" data-ready="${n.id}">${n.ready?'Expend':'Ready'}</button><button class="btn danger" data-delete="${n.id}">Delete</button></div>`:''}</article>`;}
  function renderJournal(){app.innerHTML=`<div class="panel-title"><div><p class="eyebrow">JOURNAL</p><h2>Battle Record</h2><p>Automatic game-state and Threat history.</p></div><button class="btn ghost" id="clearJournal">Clear</button></div><section class="card"><ol class="activity-log">${state.journal.length?state.journal.map(j=>`<li><time>${new Date(j.time).toLocaleString()}</time>${escapeHtml(j.text)}</li>`).join(''):'<li>No events recorded.</li>'}</ol></section>`;$('#clearJournal').onclick=()=>{state.journal=[];save();render();};}
  function renderHelp(){app.innerHTML=`<div class="panel-title"><div><p class="eyebrow">FIELD HELP</p><h2>Quick explanations</h2><p>Open an item without leaving the current game.</p></div></div><section class="card help-list">
    <details><summary>What does Enemy mean?</summary><p>Your solo player-controlled Kill Team operatives. Prompts are written from an NPO’s perspective, so your models are the NPO’s enemies.</p></details>
    <details><summary>What is an NPO?</summary><p>A non-player operative controlled by the Guide’s decision tree.</p></details>
    <details><summary>What is Threat Level?</summary><p>A 0–15 alert meter that rises from loud or destructive actions. Higher Threat produces higher grades, more reinforcements, and eventually Tomb World events.</p></details>
    <details><summary>What is Threat Grade?</summary><p>Grade 0 at Threat 0, Grade 1 at 1–5, Grade 2 at 6–10, and Grade 3 at 11–15. Reinforcements normally equal the current grade after Turning Point 1.</p></details>
    <details><summary>When do I start the next Turning Point?</summary><p>After every ready Enemy operative and NPO has activated, complete end-of-turn scoring and press Finish Turning Point. The Play tab will then offer Start Next Turning Point.</p></details>
    <details><summary>How are saves and damage handled?</summary><p>V1 focuses on setup and guided activations. Use the Roster tab to adjust NPO wounds. A full attack and save resolver is planned for the next gameplay release.</p></details>
  </section>`;}

  function boardSvg(id){const m=maps[id];const orient=mission().orientation;let zone=orient==='left'?'<rect x="30" y="30" width="110" height="430" fill="#244b74" opacity=".48"/><text x="85" y="250" fill="#a8d6ff" text-anchor="middle" transform="rotate(-90 85 250)">ENEMY DROP ZONE</text>':'<rect x="30" y="390" width="740" height="70" fill="#244b74" opacity=".48"/><text x="400" y="432" fill="#a8d6ff" text-anchor="middle">ENEMY DROP ZONE</text>';return `<div class="board-map"><svg viewBox="0 0 800 490" role="img" aria-label="Simplified board layout for ${mission().name}"><rect x="20" y="20" width="760" height="450" rx="10" fill="#08150f" stroke="#3e7558" stroke-width="3"/>${zone}<rect x="140" y="30" width="630" height="350" fill="#173721" opacity=".2"/><text x="610" y="55" fill="#7ee9a5" font-size="15">NPO TERRITORY</text>${m.walls.map(w=>`<line x1="${w[0]}" y1="${w[1]}" x2="${w[2]}" y2="${w[3]}" stroke="#80958a" stroke-width="12" stroke-linecap="square"/>`).join('')}${m.hatches.map(h=>h[2]==='v'?`<rect x="${h[0]-7}" y="${h[1]-20}" width="14" height="40" rx="4" fill="#67df99"/>`:`<rect x="${h[0]-20}" y="${h[1]-7}" width="40" height="14" rx="4" fill="#67df99"/>`).join('')}${m.markers.map(x=>`<circle cx="${x[0]}" cy="${x[1]}" r="21" fill="#b98732" stroke="#f0d074" stroke-width="3"/><text x="${x[0]}" y="${x[1]+5}" text-anchor="middle" fill="#fff" font-size="11" font-weight="800">${x[2]}</text>`).join('')}</svg></div>`;}
  function rosterBreakdown(){const counts={};state.roster.forEach(n=>counts[n.type]=(counts[n.type]||0)+1);return Object.entries(counts).map(([k,v])=>`${v} ${k}${v>1?'s':''}`).join(' · ')||'No starting NPOs';}
  function showAddNpo(){showModal('Add NPO',`<div class="field"><label>NPO type</label><select id="newNpoType">${Object.keys(profiles).map(x=>`<option>${x}</option>`).join('')}</select></div><div class="wizard-actions"><button class="btn ghost" data-close>Cancel</button><button class="btn primary" id="confirmAdd">Add NPO</button></div>`);$('#confirmAdd').onclick=()=>{const type=$('#newNpoType').value,p=profiles[type];state.roster.push({id:uid(),name:`${type} ${state.roster.length+1}`,type,behavior:p.behavior,maxWounds:p.wounds,wounds:p.wounds,save:p.save,attack:{...p.attack},ready:true,deployed:true});log(`${type} added to the battlefield.`);closeModal();save();render();};}
  function adjustWounds(id,d){const n=state.roster.find(x=>x.id===id);if(!n)return;n.wounds=Math.max(0,Math.min(n.maxWounds,n.wounds+d));if(n.wounds===0)n.ready=false;save();render();}
  function toggleReady(id){const n=state.roster.find(x=>x.id===id);if(n&&n.wounds>0)n.ready=!n.ready;save();render();}
  function deleteNpo(id){state.roster=state.roster.filter(x=>x.id!==id);save();render();}

  function showModal(title,content,onClose){modalBody.innerHTML=`<div class="modal-inner"><h2>${title}</h2>${content}</div>`;modal.showModal();modal._onClose=onClose;$$('[data-close]',modal).forEach(b=>b.onclick=closeModal);}
  function closeModal(){if(modal.open)modal.close();const cb=modal._onClose;modal._onClose=null;if(cb)cb();}
  modal.addEventListener('cancel',e=>{e.preventDefault();closeModal();});
  function showToast(text){toast.textContent=text;toast.hidden=false;clearTimeout(showToast.t);showToast.t=setTimeout(()=>toast.hidden=true,6500);}
  function confirmNewGame(){showModal('Start New Game?',`<p>This will replace the current mission, roster, Threat, Turning Point, and Journal.</p><div class="wizard-actions"><button class="btn ghost" data-close>Cancel</button><button class="btn danger" id="confirmNewGame">Start New Game</button></div>`);$('#confirmNewGame').onclick=()=>{localStorage.removeItem(STORAGE_KEY);state=initialState();state.screen='setup';closeModal();save();render();};}
  function exportSave(){const blob=new Blob([JSON.stringify(state,null,2)],{type:'application/json'}),a=document.createElement('a');a.href=URL.createObjectURL(blob);a.download='tomb-world-solo-guide-save.json';a.click();URL.revokeObjectURL(a.href);}
  importInput.addEventListener('change',async()=>{const f=importInput.files?.[0];if(!f)return;try{const data=JSON.parse(await f.text());if(!data.version)throw new Error();state=data;state.screen='game';save();render();showToast('Save imported.');}catch{showToast('That file is not a valid Tomb World Solo Guide save.');}finally{importInput.value='';}});

  function bindCommon(){
    $$('#bottomNav button').forEach(b=>b.onclick=()=>{state.tab=b.dataset.nav;save();render();});
  }

  render();
})();
